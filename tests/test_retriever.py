"""
Tests for RAG Retriever Module
Tests event retrieval with semantic search and filtering logic.
"""

from datetime import date
from pathlib import Path

import pytest

from adk.rag.embeddings import HashEmbeddings
from adk.rag.retriever import EventRetriever
from adk.rag.vector_store_faiss import FaissVectorStore
from adk.models.schemas import Event


# Test data paths
EVENTS_PATH = Path(__file__).parent.parent / "data" / "events.yaml"
EMBEDDINGS_PATH = Path(__file__).parent.parent / "data" / "embeddings_v1.json"


class TestVectorStoreFiltering:
    """Test filtering logic in FaissVectorStore."""
    
    def test_haversine_distance(self):
        """Test geographic distance calculation."""
        store = FaissVectorStore(dim=384)
        
        # Same location
        lat, lon = 41.3851, 2.1734
        distance = store._haversine_distance(lat, lon, lat, lon)
        assert distance == 0.0
        
        # Known distance: Sagrada Familia to Park Güell (roughly 2.5km)
        sagrada = (41.4036, 2.1744)
        park_guell = (41.4145, 2.1527)
        distance = store._haversine_distance(*sagrada, *park_guell)
        assert 2.0 < distance < 3.0
        
        # Symmetric
        d1 = store._haversine_distance(41.3851, 2.1734, 41.4036, 2.1744)
        d2 = store._haversine_distance(41.4036, 2.1744, 41.3851, 2.1734)
        assert abs(d1 - d2) < 0.001
    
    def test_passes_filters_tags(self):
        """Test tag filtering logic."""
        store = FaissVectorStore(dim=384)
        
        meta = {'tags': ['modern', 'photography']}
        
        # Match
        passes, _ = store._passes_filters(meta, {'tags': ['modern']})
        assert passes
        
        # No match
        passes, _ = store._passes_filters(meta, {'tags': ['baroque']})
        assert not passes
    
    def test_passes_filters_dates(self):
        """Test date range filtering logic."""
        store = FaissVectorStore(dim=384)
        
        meta = {
            'start_date': '2025-11-01',
            'end_date': '2025-12-31'
        }
        
        # Within range
        passes, _ = store._passes_filters(meta, {
            'date_range': {
                'start': date(2025, 11, 15),
                'end': date(2025, 12, 15)
            }
        })
        assert passes
        
        # No overlap (before)
        passes, _ = store._passes_filters(meta, {
            'date_range': {
                'start': date(2025, 9, 1),
                'end': date(2025, 10, 31)
            }
        })
        assert not passes
        
        # Unknown dates
        meta_unknown = {'start_date': 'unknown', 'end_date': 'unknown'}
        passes, _ = store._passes_filters(meta_unknown, {
            'date_range': {'start': date(2025, 11, 1)}
        })
        assert not passes
    
    def test_passes_filters_geo(self):
        """Test geographic filtering logic."""
        store = FaissVectorStore(dim=384)
        
        meta = {
            'latitude': 41.3851,
            'longitude': 2.1734
        }
        
        # Within radius
        passes, distance = store._passes_filters(meta, {
            'geo': {
                'lat': 41.3851,
                'lon': 2.1734,
                'radius_km': 1.0
            }
        })
        assert passes
        assert distance == 0.0
        
        # Outside radius
        passes, distance = store._passes_filters(meta, {
            'geo': {
                'lat': 41.4036,  # Sagrada Familia (~2km away)
                'lon': 2.1744,
                'radius_km': 1.0
            }
        })
        assert not passes


class TestHaversineDistance:
    """Test geographic distance calculation (legacy compatibility)."""
    
    def test_zero_distance(self):
        """Same location should have zero distance."""
        store = FaissVectorStore(dim=384)
        lat, lon = 41.3851, 2.1734
        distance = store._haversine_distance(lat, lon, lat, lon)
        assert distance == 0.0
    
    def test_known_distance(self):
        """Test with known Barcelona landmarks."""
        store = FaissVectorStore(dim=384)
        # Sagrada Familia to Park Güell (roughly 2.5km)
        sagrada = (41.4036, 2.1744)
        park_guell = (41.4145, 2.1527)
        distance = store._haversine_distance(*sagrada, *park_guell)
        assert 2.0 < distance < 3.0  # Rough validation
    
    def test_symmetric(self):
        """Distance should be symmetric."""
        store = FaissVectorStore(dim=384)
        lat1, lon1 = 41.3851, 2.1734
        lat2, lon2 = 41.4036, 2.1744
        d1 = store._haversine_distance(lat1, lon1, lat2, lon2)
        d2 = store._haversine_distance(lat2, lon2, lat1, lon1)
        assert abs(d1 - d2) < 0.001


class TestEventRetriever:
    """Test high-level EventRetriever integration."""
    
    @pytest.fixture
    def retriever(self):
        """Create retriever with hash embeddings for testing."""
        if not EVENTS_PATH.exists():
            pytest.skip("events.yaml not found")
        
        # Use hash embeddings for deterministic tests
        embeddings = HashEmbeddings(dim=384)
        vector_store = FaissVectorStore(dim=384)
        
        retriever = EventRetriever(
            events_path=EVENTS_PATH,
            vector_store=vector_store,
            embeddings=embeddings
        )
        
        # Load precomputed embeddings if available
        if EMBEDDINGS_PATH.exists():
            retriever.load_precomputed_embeddings(EMBEDDINGS_PATH)
        
        return retriever
    
    def test_basic_retrieval(self, retriever):
        """Test basic semantic search."""
        results = retriever.retrieve(query_text="modern art", top_k=5)
        assert len(results) > 0
        assert all(r.raw_score >= 0 for r in results)
        
        # Results should be sorted by score (descending)
        scores = [r.raw_score for r in results]
        assert scores == sorted(scores, reverse=True)
    
    def test_tag_filtering(self, retriever):
        """Test retrieval with tag filter."""
        results = retriever.retrieve(
            query_text="art exhibition",
            top_k=10,
            tag_filter=["photography"]
        )
        
        # All results should have photography tag
        assert all("photography" in r.tags for r in results)
    
    def test_date_filtering(self, retriever):
        """Test retrieval with date range."""
        results = retriever.retrieve(
            query_text="art events",
            top_k=10,
            date_start=date(2025, 11, 20),
            date_end=date(2025, 12, 31)
        )
        
        # All results should overlap with the date range
        for result in results:
            event = retriever.events_by_id[result.event_id]
            assert event.end_date >= date(2025, 11, 20)
            assert event.start_date <= date(2025, 12, 31)
    
    def test_geo_filtering(self, retriever):
        """Test retrieval with geographic filter."""
        # Plaça Catalunya coordinates
        results = retriever.retrieve(
            query_text="art galleries",
            top_k=10,
            geo_origin=(41.3851, 2.1734),
            geo_radius_km=2.0
        )
        
        # All results should have distance_km <= 2.0
        assert all(r.distance_km is not None for r in results)
        assert all(r.distance_km <= 2.0 for r in results)
    
    def test_combined_filters(self, retriever):
        """Test retrieval with multiple filters."""
        results = retriever.retrieve(
            query_text="modern photography",
            top_k=5,
            tag_filter=["photography", "modern"],
            date_start=date(2025, 11, 1),
            date_end=date(2026, 2, 1),
            geo_origin=(41.3851, 2.1734),
            geo_radius_km=5.0
        )
        
        # Validate all filters applied
        for result in results:
            # At least one tag should match
            assert any(tag in result.tags for tag in ["photography", "modern"])
            
            # Date overlap
            event = retriever.events_by_id[result.event_id]
            assert event.end_date >= date(2025, 11, 1)
            assert event.start_date <= date(2026, 2, 1)
            
            # Distance within radius
            assert result.distance_km is not None
            assert result.distance_km <= 5.0
    
    def test_top_k_limit(self, retriever):
        """Test that top_k limit is respected."""
        results = retriever.retrieve(query_text="art", top_k=3)
        assert len(results) <= 3
    
    def test_empty_results(self, retriever):
        """Test handling of filters that match nothing."""
        results = retriever.retrieve(
            query_text="art",
            top_k=10,
            tag_filter=["nonexistent_tag_xyz"]
        )
        assert len(results) == 0
    
    def test_metadata_complete(self, retriever):
        """Test that result metadata is complete."""
        results = retriever.retrieve(query_text="art", top_k=1)
        assert len(results) > 0
        
        result = results[0]
        assert result.event_id
        assert result.raw_score >= 0
        assert len(result.tags) > 0
        assert 'title_en' in result.metadata
        assert 'description_en' in result.metadata
        assert 'category' in result.metadata
        assert 'start_date' in result.metadata
        assert 'end_date' in result.metadata
        assert 'venue_id' in result.metadata
        assert 'cost_bucket' in result.metadata
        assert 'latitude' in result.metadata
        assert 'longitude' in result.metadata


class TestRetrieverIntegration:
    """Integration tests with real data."""
    
    @pytest.mark.skipif(not EMBEDDINGS_PATH.exists(), reason="Embeddings file not found")
    def test_modern_query_returns_modern_events(self):
        """Day 4 success metric: 'modern' query returns modern-tag events."""
        # Use real HuggingFace embeddings for semantic validation
        retriever = EventRetriever(events_path=EVENTS_PATH)
        retriever.load_precomputed_embeddings(EMBEDDINGS_PATH)
        
        results = retriever.retrieve(query_text="modern art", top_k=3)
        
        assert len(results) > 0
        
        # At least one of top-3 should have 'modern' tag
        modern_in_top3 = any("modern" in r.tags for r in results[:3])
        assert modern_in_top3, "Expected at least one modern event in top-3"
    
    @pytest.mark.skipif(not EMBEDDINGS_PATH.exists(), reason="Embeddings file not found")
    def test_photography_query_returns_photography_events(self):
        """Verify semantic search quality for photography."""
        retriever = EventRetriever(events_path=EVENTS_PATH)
        retriever.load_precomputed_embeddings(EMBEDDINGS_PATH)
        
        results = retriever.retrieve(query_text="photography exhibition", top_k=5)
        
        # At least one result should have photography tag
        photography_results = [r for r in results if "photography" in r.tags]
        assert len(photography_results) > 0
