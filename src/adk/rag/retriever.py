"""
RAG Retriever Module
Combines vector store with filtering logic to retrieve and rank event candidates.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from adk.models.schemas import DataContainer, Event, Venue
from adk.rag.embeddings import get_embeddings
from adk.rag.interfaces import EmbeddingsInterface, VectorStoreInterface
from adk.rag.vector_store_faiss import FaissVectorStore


@dataclass
class RetrievalResult:
    """Result from retrieval operation."""
    event_id: str
    raw_score: float  # Cosine similarity score
    tags: List[str]
    metadata: Dict[str, Any]  # Includes event details
    distance_km: Optional[float] = None  # Geo distance if applicable


class EventRetriever:
    """
    High-level retriever combining vector search with filtering.
    """
    
    def __init__(
        self,
        events_path: Path,
        vector_store: Optional[VectorStoreInterface] = None,
        embeddings: Optional[EmbeddingsInterface] = None
    ):
        """
        Initialize retriever.
        
        Args:
            events_path: Path to events.yaml
            vector_store: Vector store instance (creates new if None)
            embeddings: Embeddings provider (gets default if None)
        """
        self.events_path = events_path
        self.embeddings = embeddings or get_embeddings()
        self.vector_store = vector_store or FaissVectorStore(dim=self.embeddings.dim)
        
        # Load events and venues into memory
        self.events_by_id: Dict[str, Event] = {}
        self.venues_by_id: Dict[str, Venue] = {}
        self._load_data()
    
    def _load_data(self) -> None:
        """Load events and venues from YAML into memory."""
        with open(self.events_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Load DataContainer to get venues
        data_container = DataContainer(**data)
        
        # Cache events
        for event in data_container.events:
            self.events_by_id[event.id] = event
        
        # Cache venues
        for venue in data_container.venues:
            self.venues_by_id[venue.id] = venue
    
    def load_precomputed_embeddings(self, embeddings_path: Path) -> None:
        """
        Load precomputed embeddings into vector store.
        
        Args:
            embeddings_path: Path to embeddings JSON file
        """
        import json
        
        with open(embeddings_path, 'r') as f:
            data = json.load(f)
        
        # Validate dimensions match
        if data['dim'] != self.vector_store.dim:
            raise ValueError(
                f"Dimension mismatch: vector store expects {self.vector_store.dim}, "
                f"embeddings file has {data['dim']}"
            )
        
        # Batch add to vector store
        docs = []
        for doc in data['docs']:
            docs.append({
                'doc_id': doc['event_id'],
                'embedding': doc['embedding'],
                'metadata': {
                    'tags': doc['tags'],
                    'text_concat': doc.get('text_concat', '')
                }
            })
        
        self.vector_store.batch_add(docs)
    
    def retrieve(
        self,
        query_text: str,
        top_k: int = 10,
        tag_filter: Optional[List[str]] = None,
        date_start: Optional[date] = None,
        date_end: Optional[date] = None,
        geo_origin: Optional[tuple[float, float]] = None,
        geo_radius_km: Optional[float] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve events matching query with optional filters.
        
        All filtering is delegated to the vector store for efficiency.
        
        Args:
            query_text: Natural language query
            top_k: Maximum number of results
            tag_filter: Optional tags to filter by (any match)
            date_start: Start of date window
            date_end: End of date window
            geo_origin: (lat, lon) tuple for geo filtering
            geo_radius_km: Radius in km for geo filtering
        
        Returns:
            List of RetrievalResult objects sorted by raw_score (descending)
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_text(query_text)
        
        # Build filters for vector store
        filters = {}
        
        if tag_filter:
            filters['tags'] = tag_filter
        
        if date_start or date_end:
            filters['date_range'] = {}
            if date_start:
                filters['date_range']['start'] = date_start
            if date_end:
                filters['date_range']['end'] = date_end
        
        if geo_origin and geo_radius_km:
            filters['geo'] = {
                'lat': geo_origin[0],
                'lon': geo_origin[1],
                'radius_km': geo_radius_km
            }
        
        # Query vector store (all filtering happens here)
        vector_results = self.vector_store.query(
            embedding=query_embedding,
            top_k=top_k,
            filters=filters if filters else None
        )
        
        # Build results with event metadata
        results = []
        for result in vector_results:
            event = self.events_by_id.get(result['doc_id'])
            if not event:
                continue
            
            metadata = result['metadata']
            
            # Ensure dates are strings for serialization
            start_date_str = metadata.get('start_date', str(event.start_date))
            end_date_str = metadata.get('end_date', str(event.end_date))
            
            # Get venue name
            venue = self.venues_by_id.get(event.venue_id)
            venue_name = venue.name if venue else event.venue_id
            
            results.append(RetrievalResult(
                event_id=event.id,
                raw_score=result['score'],
                tags=event.tags,
                metadata={
                    'title_en': event.title_en,
                    'description_en': event.description_en,
                    'category': event.category,
                    'start_date': start_date_str,
                    'end_date': end_date_str,
                    'venue_id': event.venue_id,
                    'venue_name': venue_name,
                    'cost_bucket': event.cost_bucket,
                    'latitude': event.latitude,
                    'longitude': event.longitude,
                },
                distance_km=metadata.get('distance_km')
            ))
        
        return results
