from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import date
from math import asin, cos, radians, sin, sqrt
import json
import numpy as np
import faiss
import os

class FaissVectorStore:
    provider = "faiss"

    def __init__(self, dim: int, normalize: bool = True):
        self.dim = dim
        self.normalize = normalize
        self._index = faiss.IndexFlatIP(dim)  # inner product (assumes normalized)
        self._embeddings = []  # keep raw for potential rebuild
        self._metadata: List[Dict[str, Any]] = []
        self._id_to_pos: Dict[str, int] = {}

    def add(self, doc_id: str, embedding: List[float], metadata: Dict[str, Any]) -> None:
        vec = np.array(embedding, dtype='float32')
        if self.normalize:
            faiss.normalize_L2(vec.reshape(1, -1))
        self._index.add(vec.reshape(1, -1))
        self._embeddings.append(vec)
        self._metadata.append({"doc_id": doc_id, **metadata})
        self._id_to_pos[doc_id] = len(self._metadata) - 1

    def batch_add(self, items: List[Dict[str, Any]]) -> None:
        vectors = []
        for it in items:
            vec = np.array(it["embedding"], dtype='float32')
            if self.normalize:
                faiss.normalize_L2(vec.reshape(1, -1))
            vectors.append(vec)
            self._metadata.append({"doc_id": it["doc_id"], **it.get("metadata", {})})
            self._id_to_pos[it["doc_id"]] = len(self._metadata) - 1
        if vectors:
            mat = np.vstack(vectors)
            self._index.add(mat)
            self._embeddings.extend(vectors)

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance between two points in kilometers."""
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return 6371 * c  # Earth radius in km

    def _passes_filters(self, meta: Dict[str, Any], filters: Dict[str, Any]) -> tuple[bool, Optional[float]]:
        """
        Check if metadata passes all filters.
        
        Args:
            meta: Document metadata
            filters: Filter dict with keys: tags, date_range, geo
        
        Returns:
            (passes, distance_km) tuple
        """
        distance_km = None
        
        # Tag filter
        if "tags" in filters:
            if not set(filters["tags"]).intersection(set(meta.get("tags", []))):
                return False, None
        
        # Date range filter
        if "date_range" in filters:
            date_range = filters["date_range"]
            start_filter = date_range.get("start")
            end_filter = date_range.get("end")
            
            # Skip events with unknown dates
            event_start = meta.get("start_date")
            event_end = meta.get("end_date")
            
            if event_start == "unknown" or event_end == "unknown":
                return False, None
            
            try:
                event_start_date = date.fromisoformat(event_start)
                event_end_date = date.fromisoformat(event_end)
                
                # Check overlap: event overlaps filter if event.end >= filter.start AND event.start <= filter.end
                if start_filter and event_end_date < start_filter:
                    return False, None
                if end_filter and event_start_date > end_filter:
                    return False, None
            except (ValueError, TypeError):
                return False, None
        
        # Geo filter
        if "geo" in filters:
            geo = filters["geo"]
            origin_lat = geo.get("lat")
            origin_lon = geo.get("lon")
            radius_km = geo.get("radius_km")
            
            event_lat = meta.get("latitude")
            event_lon = meta.get("longitude")
            
            if origin_lat is not None and origin_lon is not None and radius_km is not None:
                if event_lat is None or event_lon is None:
                    return False, None
                
                distance_km = self._haversine_distance(origin_lat, origin_lon, event_lat, event_lon)
                if distance_km > radius_km:
                    return False, None
        
        return True, distance_km

    def query(self, embedding: List[float], top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Query vector store with optional filters.
        
        Args:
            embedding: Query embedding vector
            top_k: Number of results to return
            filters: Optional filter dict with keys:
                - tags: List[str] - Tag filter (any match)
                - date_range: {start: date, end: date} - Date range filter
                - geo: {lat: float, lon: float, radius_km: float} - Geographic filter
        
        Returns:
            List of results with doc_id, score, metadata (and distance_km if geo filter applied)
        """
        # Handle empty store
        if len(self._metadata) == 0:
            return []
        
        q = np.array(embedding, dtype='float32')
        if self.normalize:
            faiss.normalize_L2(q.reshape(1, -1))
        
        # Fetch more results than needed to account for filtering
        search_k = top_k * 5 if filters else top_k
        scores, idxs = self._index.search(q.reshape(1, -1), min(search_k, len(self._metadata)))
        
        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            
            meta = self._metadata[idx]
            
            # Apply filters
            if filters:
                passes, distance_km = self._passes_filters(meta, filters)
                if not passes:
                    continue
                
                # Add distance to metadata if geo filter was applied
                if distance_km is not None:
                    meta = {**meta, "distance_km": distance_km}
            
            results.append({
                "doc_id": meta["doc_id"],
                "score": float(score),
                "metadata": meta
            })
            
            if len(results) >= top_k:
                break
        
        return results

    def stats(self) -> Dict[str, Any]:
        return {"count": len(self._metadata), "dim": self.dim, "provider": self.provider}

    def rebuild_index(self) -> None:
        self._index = faiss.IndexFlatIP(self.dim)
        if self._embeddings:
            mat = np.vstack(self._embeddings)
            if self.normalize:
                faiss.normalize_L2(mat)
            self._index.add(mat)
