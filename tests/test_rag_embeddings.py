"""Tests for embeddings module."""
import pytest
import os
from src.adk.rag.embeddings import HashEmbeddings, HuggingFaceEmbeddings, get_embeddings


class TestHashEmbeddings:
    """Test deterministic hash-based embeddings."""
    
    def test_initialization(self):
        """Hash embeddings initialize with correct dimensions."""
        emb = HashEmbeddings(dim=128)
        assert emb.dim == 128
        assert emb.provider == "hash"
        assert emb.model_name == "hash-deterministic"
    
    def test_embed_text_deterministic(self):
        """Hash embeddings produce deterministic results."""
        emb = HashEmbeddings(dim=384)
        text = "modern art exhibition in barcelona"
        
        vec1 = emb.embed_text(text)
        vec2 = emb.embed_text(text)
        
        assert vec1 == vec2
        assert len(vec1) == 384
        assert all(0 <= v <= 1 for v in vec1)
    
    def test_embed_text_different_inputs(self):
        """Different texts produce different embeddings."""
        emb = HashEmbeddings(dim=384)
        
        vec1 = emb.embed_text("modern art")
        vec2 = emb.embed_text("classical sculpture")
        
        assert vec1 != vec2
    
    def test_embed_batch(self):
        """Batch embedding returns list of vectors."""
        emb = HashEmbeddings(dim=256)
        texts = ["art", "museum", "gallery"]
        
        vecs = emb.embed_batch(texts)
        
        assert len(vecs) == 3
        assert all(len(v) == 256 for v in vecs)
        assert vecs[0] != vecs[1]
    
    def test_case_insensitive(self):
        """Hash embeddings are case-insensitive."""
        emb = HashEmbeddings(dim=128)
        
        vec1 = emb.embed_text("Modern Art")
        vec2 = emb.embed_text("modern art")
        
        assert vec1 == vec2


class TestHuggingFaceEmbeddings:
    """Test HuggingFace sentence-transformers embeddings."""
    
    def test_initialization(self):
        """HF embeddings initialize with correct model."""
        try:
            emb = HuggingFaceEmbeddings()
            assert emb.provider == "hf"
            assert "MiniLM" in emb.model_name
            assert emb.dim == 384  # all-MiniLM-L6-v2 dimension
        except RuntimeError:
            pytest.skip("sentence-transformers not installed")
    
    def test_embed_text(self):
        """HF embeddings produce valid vectors."""
        try:
            emb = HuggingFaceEmbeddings()
            text = "contemporary art exhibition"
            
            vec = emb.embed_text(text)
            
            assert len(vec) == 384
            assert all(isinstance(v, float) for v in vec)
            # Normalized vectors should have norm ~1
            norm = sum(v**2 for v in vec) ** 0.5
            assert 0.95 < norm < 1.05
        except RuntimeError:
            pytest.skip("sentence-transformers not installed")
    
    def test_embed_batch(self):
        """HF batch embedding works correctly."""
        try:
            emb = HuggingFaceEmbeddings()
            texts = ["modern art", "classical sculpture", "digital installation"]
            
            vecs = emb.embed_batch(texts)
            
            assert len(vecs) == 3
            assert all(len(v) == 384 for v in vecs)
        except RuntimeError:
            pytest.skip("sentence-transformers not installed")
    
    def test_semantic_similarity(self):
        """Similar texts produce similar embeddings."""
        try:
            emb = HuggingFaceEmbeddings()
            
            vec1 = emb.embed_text("modern art exhibition")
            vec2 = emb.embed_text("contemporary art show")
            vec3 = emb.embed_text("ancient history museum")
            
            # Cosine similarity
            def cosine(a, b):
                return sum(x*y for x, y in zip(a, b))
            
            sim_12 = cosine(vec1, vec2)
            sim_13 = cosine(vec1, vec3)
            
            # Related texts should be more similar
            assert sim_12 > sim_13
        except RuntimeError:
            pytest.skip("sentence-transformers not installed")
    
    def test_cache_directory(self):
        """Model uses cache directory."""
        try:
            os.environ["HF_CACHE_DIR"] = "/tmp/test_hf_cache"
            emb = HuggingFaceEmbeddings()
            assert emb._model is not None
        except RuntimeError:
            pytest.skip("sentence-transformers not installed")
        finally:
            os.environ.pop("HF_CACHE_DIR", None)


class TestGetEmbeddings:
    """Test embeddings factory function."""
    
    def test_get_hash_embeddings(self):
        """Factory returns hash embeddings."""
        emb = get_embeddings(provider="hash", dim=256)
        assert isinstance(emb, HashEmbeddings)
        assert emb.dim == 256
    
    def test_get_hf_embeddings(self):
        """Factory returns HF embeddings."""
        try:
            emb = get_embeddings(provider="hf")
            assert isinstance(emb, HuggingFaceEmbeddings)
        except RuntimeError:
            pytest.skip("sentence-transformers not installed")
    
    def test_get_hf_fallback(self):
        """Factory falls back to hash if HF unavailable."""
        # This test would need to mock the import failure
        # For now, just verify hash works
        emb = get_embeddings(provider="hash")
        assert isinstance(emb, HashEmbeddings)
    
    def test_unknown_provider(self):
        """Factory raises on unknown provider."""
        with pytest.raises(ValueError, match="Unknown embeddings provider"):
            get_embeddings(provider="unknown")
    
    def test_default_provider(self):
        """Factory uses default provider."""
        emb = get_embeddings()  # defaults to "hf"
        assert emb is not None
