from __future__ import annotations
from typing import List, Dict, Any, Optional
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

    def query(self, embedding: List[float], top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        q = np.array(embedding, dtype='float32')
        if self.normalize:
            faiss.normalize_L2(q.reshape(1, -1))
        scores, idxs = self._index.search(q.reshape(1, -1), top_k * 2)
        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            meta = self._metadata[idx]
            if filters:
                if "tags" in filters:
                    if not set(filters["tags"]).intersection(set(meta.get("tags", []))):
                        continue
            results.append({"doc_id": meta["doc_id"], "score": float(score), "metadata": meta})
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
