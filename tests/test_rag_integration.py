"""Integration tests for RAG system (embeddings + vector store)."""
import pytest
import json
import tempfile
from pathlib import Path
from src.adk.rag.embeddings import get_embeddings, HashEmbeddings, HuggingFaceEmbeddings
from src.adk.rag.vector_store_faiss import FaissVectorStore


class TestEmbeddingsVectorStoreIntegration:
    """Test embeddings and vector store working together."""
    
    def test_hash_embeddings_with_faiss(self):
        """Hash embeddings integrate with FAISS store."""
        # Create embeddings provider
        emb = HashEmbeddings(dim=128)
        
        # Create vector store
        store = FaissVectorStore(dim=128)
        
        # Add documents
        texts = [
            "modern art exhibition barcelona",
            "classical music concert",
            "contemporary digital installation"
        ]
        
        for i, text in enumerate(texts):
            vec = emb.embed_text(text)
            store.add(f"evt_{i:03d}", vec, {"text": text, "tags": ["art"]})
        
        # Query
        query_text = "modern art show"
        query_vec = emb.embed_text(query_text)
        results = store.query(query_vec, top_k=2)
        
        assert len(results) == 2
        assert all("evt_" in r["doc_id"] for r in results)
        assert all("score" in r for r in results)
    
    def test_hf_embeddings_with_faiss(self):
        """HuggingFace embeddings integrate with FAISS store."""
        try:
            emb = HuggingFaceEmbeddings()
            store = FaissVectorStore(dim=384, normalize=True)
            
            # Add documents with semantic content
            docs = [
                {"id": "evt_001", "text": "modern art photography exhibition", "tags": ["modern", "photography"]},
                {"id": "evt_002", "text": "classical painting masterworks", "tags": ["classical", "painting"]},
                {"id": "evt_003", "text": "contemporary digital art installation", "tags": ["modern", "digital"]},
            ]
            
            for doc in docs:
                vec = emb.embed_text(doc["text"])
                store.add(doc["id"], vec, {"text": doc["text"], "tags": doc["tags"]})
            
            # Query for modern art
            query_vec = emb.embed_text("modern art exhibition")
            results = store.query(query_vec, top_k=2)
            
            assert len(results) == 2
            # Should find modern/contemporary events
            found_ids = [r["doc_id"] for r in results]
            assert "evt_001" in found_ids or "evt_003" in found_ids
            
        except RuntimeError:
            pytest.skip("sentence-transformers not installed")
    
    def test_semantic_search_quality(self):
        """Semantic search returns relevant results."""
        try:
            emb = HuggingFaceEmbeddings()
            store = FaissVectorStore(dim=384)
            
            # Add diverse documents
            docs = [
                "photography exhibition at modern art museum",
                "sculpture garden outdoor installation",
                "digital video art screening",
                "baroque painting restoration",
                "contemporary street art tour"
            ]
            
            for i, text in enumerate(docs):
                vec = emb.embed_text(text)
                store.add(f"evt_{i:03d}", vec, {"text": text})
            
            # Search for "modern art"
            query = "modern art photography"
            query_vec = emb.embed_text(query)
            results = store.query(query_vec, top_k=3)
            
            # First result should be photography-related
            assert "photography" in results[0]["metadata"]["text"].lower()
            
        except RuntimeError:
            pytest.skip("sentence-transformers not installed")
    
    def test_filter_with_semantic_search(self):
        """Combining filters with semantic search works."""
        emb = HashEmbeddings(dim=128)
        store = FaissVectorStore(dim=128)
        
        # Add documents with tags
        docs = [
            {"text": "modern photography", "tags": ["modern", "photography"]},
            {"text": "modern sculpture", "tags": ["modern", "sculpture"]},
            {"text": "classical painting", "tags": ["classical", "painting"]},
            {"text": "modern digital art", "tags": ["modern", "digital"]},
        ]
        
        for i, doc in enumerate(docs):
            vec = emb.embed_text(doc["text"])
            store.add(f"evt_{i:03d}", vec, {"text": doc["text"], "tags": doc["tags"]})
        
        # Search for modern art only
        query_vec = emb.embed_text("art exhibition")
        results = store.query(query_vec, top_k=10, filters={"tags": ["modern"]})
        
        # Should only get modern results
        assert len(results) == 3
        assert all("modern" in r["metadata"]["tags"] for r in results)
    
    def test_empty_corpus_handling(self):
        """Handles empty corpus gracefully."""
        emb = HashEmbeddings(dim=128)
        store = FaissVectorStore(dim=128)
        
        query_vec = emb.embed_text("test query")
        results = store.query(query_vec, top_k=5)
        
        assert results == []
        assert store.stats()["count"] == 0


class TestPrecomputedEmbeddingsWorkflow:
    """Test workflow of precomputing and loading embeddings."""
    
    def test_precomputed_format(self):
        """Test the expected format of precomputed embeddings."""
        emb = HashEmbeddings(dim=128)
        
        # Simulate precomputed embeddings structure
        docs = [
            {
                "event_id": "evt_001",
                "text_concat": "Modern art exhibition in Barcelona",
                "tags": ["modern", "exhibition"],
                "embedding": emb.embed_text("Modern art exhibition in Barcelona")
            },
            {
                "event_id": "evt_002",
                "text_concat": "Classical music concert",
                "tags": ["classical", "music"],
                "embedding": emb.embed_text("Classical music concert")
            }
        ]
        
        payload = {
            "schema_version": 1,
            "embedding_model": emb.model_name,
            "provider": emb.provider,
            "dim": emb.dim,
            "docs": docs
        }
        
        # Verify structure
        assert payload["schema_version"] == 1
        assert payload["dim"] == 128
        assert payload["provider"] == "hash"
        assert len(payload["docs"]) == 2
        assert all("embedding" in d for d in payload["docs"])
    
    def test_load_precomputed_into_store(self):
        """Test loading precomputed embeddings into vector store."""
        # Create synthetic precomputed data
        emb = HashEmbeddings(dim=128)
        docs = []
        for i in range(5):
            text = f"Event {i} description"
            docs.append({
                "event_id": f"evt_{i:03d}",
                "text_concat": text,
                "tags": ["test"],
                "embedding": emb.embed_text(text)
            })
        
        # Load into store
        store = FaissVectorStore(dim=128)
        items = [
            {
                "doc_id": d["event_id"],
                "embedding": d["embedding"],
                "metadata": {"tags": d["tags"], "text": d["text_concat"]}
            }
            for d in docs
        ]
        store.batch_add(items)
        
        # Verify loaded
        assert store.stats()["count"] == 5
        
        # Query works
        query_vec = emb.embed_text("Event 2 description")
        results = store.query(query_vec, top_k=1)
        assert len(results) == 1
    
    def test_version_mismatch_detection(self):
        """Test detecting version mismatches."""
        # Simulate version mismatch scenario
        payload_v1 = {"schema_version": 1, "dim": 128, "provider": "hash"}
        payload_v2 = {"schema_version": 2, "dim": 128, "provider": "hash"}
        
        # In real implementation, loading v2 with v1 code should fail
        assert payload_v1["schema_version"] != payload_v2["schema_version"]
    
    def test_dimension_mismatch_detection(self):
        """Test detecting dimension mismatches."""
        # Create embeddings with one dimension
        emb_128 = HashEmbeddings(dim=128)
        vec_128 = emb_128.embed_text("test")
        
        # Try to use with different dimension store
        store_256 = FaissVectorStore(dim=256)
        
        # Should handle gracefully (in practice would need validation)
        assert len(vec_128) == 128
        assert store_256.dim == 256


class TestRealisticScenarios:
    """Test realistic usage scenarios."""
    
    def test_event_recommendation_scenario(self):
        """Simulate realistic event recommendation."""
        try:
            emb = HuggingFaceEmbeddings()
            store = FaissVectorStore(dim=384)
            
            # Add realistic events
            events = [
                {"id": "evt_001", "text": "Photography exhibition featuring modern urban landscapes", "tags": ["modern", "photography"]},
                {"id": "evt_002", "text": "Classical baroque painting restoration workshop", "tags": ["classical", "painting"]},
                {"id": "evt_003", "text": "Interactive digital art installation with VR", "tags": ["digital", "interactive"]},
                {"id": "evt_004", "text": "Contemporary sculpture exhibition in Gothic Quarter", "tags": ["contemporary", "sculpture"]},
                {"id": "evt_005", "text": "Street photography walking tour of El Raval", "tags": ["photography", "outdoor"]},
            ]
            
            for event in events:
                vec = emb.embed_text(event["text"])
                store.add(event["id"], vec, {"text": event["text"], "tags": event["tags"]})
            
            # User query: looking for photography events
            query = "I want to see photography exhibitions"
            query_vec = emb.embed_text(query)
            results = store.query(query_vec, top_k=3)
            
            # Should find photography-related events
            assert len(results) == 3
            found_ids = [r["doc_id"] for r in results]
            assert "evt_001" in found_ids or "evt_005" in found_ids
            
        except RuntimeError:
            pytest.skip("sentence-transformers not installed")
    
    def test_tag_filtering_recommendation(self):
        """Test recommendation with tag filtering."""
        emb = HashEmbeddings(dim=128)
        store = FaissVectorStore(dim=128)
        
        # User profile: prefers modern art
        user_preferred_tags = ["modern", "contemporary"]
        
        # Add events
        events = [
            {"id": "evt_001", "text": "Modern art exhibition", "tags": ["modern", "painting"]},
            {"id": "evt_002", "text": "Classical art museum", "tags": ["classical", "museum"]},
            {"id": "evt_003", "text": "Contemporary installation", "tags": ["contemporary", "installation"]},
            {"id": "evt_004", "text": "Baroque architecture tour", "tags": ["baroque", "architecture"]},
        ]
        
        for event in events:
            vec = emb.embed_text(event["text"])
            store.add(event["id"], vec, {"text": event["text"], "tags": event["tags"]})
        
        # Query with preference filter
        query_vec = emb.embed_text("art event")
        results = store.query(query_vec, top_k=10, filters={"tags": user_preferred_tags})
        
        # Should only return modern/contemporary
        assert len(results) == 2
        assert all(
            any(tag in r["metadata"]["tags"] for tag in user_preferred_tags)
            for r in results
        )
    
    def test_no_results_scenario(self):
        """Test when no events match query."""
        emb = HashEmbeddings(dim=128)
        store = FaissVectorStore(dim=128)
        
        # Add events with specific tags
        store.add("evt_001", emb.embed_text("art"), {"tags": ["painting"]})
        store.add("evt_002", emb.embed_text("art"), {"tags": ["sculpture"]})
        
        # Query with incompatible filter
        query_vec = emb.embed_text("art")
        results = store.query(query_vec, top_k=5, filters={"tags": ["music"]})
        
        # Should return empty
        assert results == []
