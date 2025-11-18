"""
ADK Tool: retrieve_events

Retrieves art events from Barcelona using semantic search and filters.
This tool integrates the RAG infrastructure with ADK's tool framework.
"""

from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from adk.rag.retriever import EventRetriever


@dataclass
class RetrieveEventsInput:
    """Input schema for retrieve_events tool."""
    query_text: str
    max_results: int = 10
    tags: Optional[List[str]] = None
    date_start: Optional[str] = None  # ISO format YYYY-MM-DD
    date_end: Optional[str] = None    # ISO format YYYY-MM-DD
    geo_lat: Optional[float] = None
    geo_lon: Optional[float] = None
    geo_radius_km: Optional[float] = None


@dataclass
class EventResult:
    """Single event result."""
    event_id: str
    title: str
    description: str
    tags: List[str]
    category: str
    start_date: str
    end_date: str
    venue_id: str
    venue_name: str  # Venue name for display
    cost_bucket: str
    latitude: float
    longitude: float
    raw_score: float
    distance_km: Optional[float] = None


@dataclass
class RetrieveEventsOutput:
    """Output schema for retrieve_events tool."""
    events: List[EventResult]
    total_found: int
    query: str
    filters_applied: Dict[str, Any]


# Global retriever instance (initialized lazily)
_retriever: Optional[EventRetriever] = None


def get_retriever() -> EventRetriever:
    """
    Get or create the global EventRetriever instance.
    
    Returns:
        Initialized EventRetriever with precomputed embeddings loaded
    """
    global _retriever
    
    if _retriever is None:
        # Determine paths (relative to project root)
        project_root = Path(__file__).parent.parent.parent.parent
        events_path = project_root / "data" / "events.yaml"
        embeddings_path = project_root / "data" / "embeddings_v1.json"
        
        # Initialize retriever
        _retriever = EventRetriever(events_path=events_path)
        
        # Load precomputed embeddings
        if embeddings_path.exists():
            _retriever.load_precomputed_embeddings(embeddings_path)
        else:
            raise FileNotFoundError(
                f"Embeddings file not found: {embeddings_path}. "
                "Run scripts/precompute_embeddings.py first."
            )
    
    return _retriever


def retrieve_events(input_data: RetrieveEventsInput) -> RetrieveEventsOutput:
    """
    ADK Tool: Retrieve art events using semantic search and filters.
    
    Args:
        input_data: RetrieveEventsInput with query and optional filters
    
    Returns:
        RetrieveEventsOutput with ranked events and metadata
    
    Example:
        >>> input_data = RetrieveEventsInput(
        ...     query_text="modern photography exhibitions",
        ...     max_results=5,
        ...     tags=["photography", "modern"],
        ...     date_start="2025-11-20",
        ...     date_end="2026-01-31"
        ... )
        >>> output = retrieve_events(input_data)
        >>> print(f"Found {output.total_found} events")
        >>> for event in output.events:
        ...     print(f"- {event.title} (score: {event.raw_score:.3f})")
    """
    retriever = get_retriever()
    
    # Parse date filters
    date_start = date.fromisoformat(input_data.date_start) if input_data.date_start else None
    date_end = date.fromisoformat(input_data.date_end) if input_data.date_end else None
    
    # Parse geo filters
    geo_origin = None
    if input_data.geo_lat is not None and input_data.geo_lon is not None:
        geo_origin = (input_data.geo_lat, input_data.geo_lon)
    
    # Execute retrieval
    results = retriever.retrieve(
        query_text=input_data.query_text,
        top_k=input_data.max_results,
        tag_filter=input_data.tags,
        date_start=date_start,
        date_end=date_end,
        geo_origin=geo_origin,
        geo_radius_km=input_data.geo_radius_km
    )
    
    # Build output
    events = []
    for result in results:
        events.append(EventResult(
            event_id=result.event_id,
            title=result.metadata['title_en'],
            description=result.metadata['description_en'],
            tags=result.tags,
            category=result.metadata['category'],
            start_date=result.metadata['start_date'],
            end_date=result.metadata['end_date'],
            venue_id=result.metadata['venue_id'],
            venue_name=result.metadata['venue_name'],
            cost_bucket=result.metadata['cost_bucket'],
            latitude=result.metadata['latitude'],
            longitude=result.metadata['longitude'],
            raw_score=result.raw_score,
            distance_km=result.distance_km
        ))
    
    # Track applied filters
    filters_applied = {}
    if input_data.tags:
        filters_applied['tags'] = input_data.tags
    if date_start or date_end:
        filters_applied['date_range'] = {
            'start': input_data.date_start,
            'end': input_data.date_end
        }
    if geo_origin:
        filters_applied['geo'] = {
            'lat': input_data.geo_lat,
            'lon': input_data.geo_lon,
            'radius_km': input_data.geo_radius_km
        }
    
    return RetrieveEventsOutput(
        events=events,
        total_found=len(events),
        query=input_data.query_text,
        filters_applied=filters_applied
    )


# ADK Tool Registration Metadata
TOOL_METADATA = {
    "name": "retrieve_events",
    "description": (
        "Retrieve Barcelona art events using semantic search. "
        "Supports filtering by tags, date range, and geographic location. "
        "Returns events ranked by relevance to the query."
    ),
    "input_schema": RetrieveEventsInput,
    "output_schema": RetrieveEventsOutput,
    "examples": [
        {
            "input": {
                "query_text": "modern photography",
                "max_results": 5,
                "tags": ["photography", "modern"]
            },
            "description": "Find modern photography events"
        },
        {
            "input": {
                "query_text": "family friendly art",
                "max_results": 3,
                "tags": ["family-friendly"],
                "date_start": "2025-12-01",
                "date_end": "2025-12-31"
            },
            "description": "Find family-friendly events in December"
        },
        {
            "input": {
                "query_text": "contemporary galleries",
                "max_results": 5,
                "geo_lat": 41.3851,
                "geo_lon": 2.1734,
                "geo_radius_km": 2.0
            },
            "description": "Find contemporary art within 2km of center"
        }
    ]
}
