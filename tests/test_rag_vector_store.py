"""Tests for FAISS vector store."""
import pytest
import numpy as np
from src.adk.rag.vector_store_faiss import FaissVectorStore


class TestFaissVectorStore:
    """Test FAISS-based vector store."""
    
    def test_initialization(self):
        """Vector store initializes correctly."""
        store = FaissVectorStore(dim=384)
        
        assert store.dim == 384
        assert store.provider == "faiss"
        assert store._index is not None
        assert store.stats()["count"] == 0
    
    def test_add_single_document(self):
        """Adding single document works."""
        store = FaissVectorStore(dim=128)
        
        embedding = [0.1] * 128
        metadata = {"tags": ["modern", "art"], "title": "Test Event"}
        
        store.add("evt_001", embedding, metadata)
        
        stats = store.stats()
        assert stats["count"] == 1
        assert "evt_001" in store._id_to_pos
    
    def test_batch_add(self):
        """Batch adding documents works."""
        store = FaissVectorStore(dim=128)
        
        items = [
            {
                "doc_id": "evt_001",
                "embedding": [0.1] * 128,
                "metadata": {"tags": ["modern"], "title": "Event 1"}
            },
            {
                "doc_id": "evt_002",
                "embedding": [0.2] * 128,
                "metadata": {"tags": ["classical"], "title": "Event 2"}
            },
            {
                "doc_id": "evt_003",
                "embedding": [0.3] * 128,
                "metadata": {"tags": ["digital"], "title": "Event 3"}
            }
        ]
        
        store.batch_add(items)
        
        stats = store.stats()
        assert stats["count"] == 3
        assert all(f"evt_00{i}" in store._id_to_pos for i in [1, 2, 3])
    
    def test_query_basic(self):
        """Basic similarity query works."""
        store = FaissVectorStore(dim=128)
        
        # Add documents with distinct embeddings
        store.add("evt_001", [1.0] + [0.0] * 127, {"tags": ["modern"]})
        store.add("evt_002", [0.0] + [1.0] + [0.0] * 126, {"tags": ["classical"]})
        store.add("evt_003", [0.9] + [0.1] + [0.0] * 126, {"tags": ["modern"]})
        
        # Query similar to evt_001
        query_vec = [1.0] + [0.0] * 127
        results = store.query(query_vec, top_k=2)
        
        assert len(results) == 2
        # evt_001 should be most similar
        assert results[0]["doc_id"] == "evt_001"
        assert results[0]["score"] > results[1]["score"]
    
    def test_query_with_tag_filter(self):
        """Tag filtering works in queries."""
        store = FaissVectorStore(dim=128)
        
        store.add("evt_001", [1.0] * 128, {"tags": ["modern", "digital"]})
        store.add("evt_002", [1.0] * 128, {"tags": ["classical", "sculpture"]})
        store.add("evt_003", [1.0] * 128, {"tags": ["modern", "painting"]})
        
        query_vec = [1.0] * 128
        results = store.query(query_vec, top_k=5, filters={"tags": ["modern"]})
        
        # Should only return modern events
        assert len(results) == 2
        assert all("modern" in r["metadata"]["tags"] for r in results)
    
    def test_query_empty_store(self):
        """Querying empty store returns empty results."""
        store = FaissVectorStore(dim=128)
        
        query_vec = [1.0] * 128
        results = store.query(query_vec, top_k=5)
        
        assert results == []
    
    def test_query_top_k_limit(self):
        """top_k parameter limits results correctly."""
        store = FaissVectorStore(dim=128)
        
        for i in range(10):
            store.add(f"evt_{i:03d}", [float(i)/10] * 128, {"tags": ["test"]})
        
        results = store.query([0.5] * 128, top_k=3)
        
        assert len(results) == 3
    
    def test_normalization(self):
        """L2 normalization is applied when enabled."""
        store = FaissVectorStore(dim=128, normalize=True)
        
        # Add unnormalized vector
        unnormalized = [3.0, 4.0] + [0.0] * 126  # norm = 5
        store.add("evt_001", unnormalized, {"tags": ["test"]})
        
        # Internal storage should be normalized
        stored = store._embeddings[0]
        norm = np.linalg.norm(stored)
        assert 0.99 < norm < 1.01
    
    def test_rebuild_index(self):
        """Index rebuild works correctly."""
        store = FaissVectorStore(dim=128)
        
        # Add documents
        for i in range(5):
            store.add(f"evt_{i:03d}", [float(i)] * 128, {"tags": ["test"]})
        
        # Rebuild index
        store.rebuild_index()
        
        # Query should still work
        results = store.query([2.0] * 128, top_k=3)
        assert len(results) == 3
        assert store.stats()["count"] == 5
    
    def test_metadata_preservation(self):
        """Metadata is preserved correctly."""
        store = FaissVectorStore(dim=128)
        
        metadata = {
            "tags": ["modern", "digital"],
            "title": "Interactive Installation",
            "venue_id": "v_01",
            "cost": "€10"
        }
        
        store.add("evt_001", [1.0] * 128, metadata)
        
        results = store.query([1.0] * 128, top_k=1)
        
        assert results[0]["metadata"]["title"] == "Interactive Installation"
        assert results[0]["metadata"]["venue_id"] == "v_01"
        assert "modern" in results[0]["metadata"]["tags"]
    
    def test_filter_no_matches(self):
        """Filter returns empty when no matches."""
        store = FaissVectorStore(dim=128)
        
        store.add("evt_001", [1.0] * 128, {"tags": ["modern"]})
        store.add("evt_002", [1.0] * 128, {"tags": ["classical"]})
        
        results = store.query([1.0] * 128, top_k=5, filters={"tags": ["digital"]})
        
        assert results == []
    
    def test_filter_intersection(self):
        """Filter matches tag intersection correctly."""
        store = FaissVectorStore(dim=128)
        
        store.add("evt_001", [1.0] * 128, {"tags": ["modern", "digital"]})
        store.add("evt_002", [1.0] * 128, {"tags": ["modern", "painting"]})
        store.add("evt_003", [1.0] * 128, {"tags": ["classical"]})
        
        # Filter for modern OR digital (should match evt_001 and evt_002)
        results = store.query([1.0] * 128, top_k=5, filters={"tags": ["modern"]})
        
        assert len(results) == 2


class TestFaissIntegration:
    """Integration tests with realistic scenarios."""
    
    def test_realistic_event_search(self):
        """Realistic event search scenario."""
        store = FaissVectorStore(dim=384)
        
        # Simulate event embeddings (would come from real model)
        events = [
            {"id": "evt_001", "tags": ["modern", "photography"], "title": "Photo Expo"},
            {"id": "evt_002", "tags": ["classical", "painting"], "title": "Masters Gallery"},
            {"id": "evt_003", "tags": ["modern", "digital"], "title": "Digital Art Fair"},
            {"id": "evt_004", "tags": ["contemporary", "sculpture"], "title": "Urban Sculptures"},
        ]
        
        # Add with synthetic embeddings
        for i, event in enumerate(events):
            embedding = [float(i)] * 384
            store.add(event["id"], embedding, {"tags": event["tags"], "title": event["title"]})
        
        # Search for modern art
        query = [0.5] * 384  # Would be real embedding
        results = store.query(query, top_k=2, filters={"tags": ["modern"]})
        
        assert len(results) <= 2
        assert all("modern" in r["metadata"]["tags"] for r in results)
    
    def test_empty_query_handling(self):
        """Handle edge cases gracefully."""
        store = FaissVectorStore(dim=128)
        store.add("evt_001", [1.0] * 128, {"tags": []})
        
        # Query with empty filter
        results = store.query([1.0] * 128, top_k=1, filters=None)
        assert len(results) == 1
        
        # Query with filter on event with no tags
        results = store.query([1.0] * 128, top_k=1, filters={"tags": ["modern"]})
        assert len(results) == 0
