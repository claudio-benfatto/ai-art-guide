from __future__ import annotations
from typing import List
import os

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover
    SentenceTransformer = None  # type: ignore

import math

class HuggingFaceEmbeddings:
    """Embeddings provider using sentence-transformers (all-MiniLM-L6-v2)."""
    provider = "hf"

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", normalize: bool = True):
        self.model_name = model_name
        self.normalize = normalize
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers not installed; cannot use HuggingFaceEmbeddings")
        # Avoid repeated downloads by using cache dir
        cache_dir = os.environ.get("HF_CACHE_DIR", os.path.join(os.getcwd(), ".hf_cache"))
        self._model = SentenceTransformer(model_name, cache_folder=cache_dir)
        # Infer dimension
        test_vec = self._model.encode(["test"], normalize_embeddings=normalize)
        self.dim = len(test_vec[0])

    def embed_text(self, text: str) -> List[float]:
        vec = self._model.encode([text], normalize_embeddings=self.normalize)[0]
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        vecs = self._model.encode(texts, normalize_embeddings=self.normalize)
        return [v.tolist() for v in vecs]

class HashEmbeddings:
    """Deterministic hash-based fallback embeddings (low quality but stable)."""
    provider = "hash"

    def __init__(self, dim: int = 384):
        self.model_name = "hash-deterministic"
        self.dim = dim

    def embed_text(self, text: str) -> List[float]:
        h = 0
        for tok in text.lower().split():
            h = (h * 33 + (hash(tok) & 0xffffffff)) & 0xffffffffffff
        return [((h + i * 997) % 1000) / 1000.0 for i in range(self.dim)]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]

def get_embeddings(provider: str = "hf", **kwargs):
    if provider == "hf":
        try:
            return HuggingFaceEmbeddings(**kwargs)
        except Exception as e:
            # Fallback to hash if model unavailable
            return HashEmbeddings()
    if provider == "hash":
        return HashEmbeddings(dim=kwargs.get("dim", 384))
    raise ValueError(f"Unknown embeddings provider: {provider}")
