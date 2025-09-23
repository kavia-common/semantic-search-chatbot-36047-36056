import os
import faiss  # type: ignore
import numpy as np
from typing import List, Tuple
from django.conf import settings
from .embedding import embed_texts

class FaissIndex:
    """
    Wrapper around a FAISS index with disk persistence.
    Maps vector order to (document_id, chunk_index) pairs.
    """
    def __init__(self, index_path: str | None = None, dim: int = 384):
        self.index_path = index_path or settings.FAISS_INDEX_PATH
        self.dim = dim
        self._index = None
        self._ids: list[tuple[int, int]] = []  # (document_id, chunk_index)

        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        self._load()

    def _load(self):
        meta_path = self.index_path + ".meta.npy"
        if os.path.exists(self.index_path) and os.path.exists(meta_path):
            self._index = faiss.read_index(self.index_path)
            self._ids = [tuple(x) for x in np.load(meta_path, allow_pickle=True).tolist()]
        else:
            self._index = faiss.IndexFlatIP(self.dim)  # cosine if vectors are normalized
            self._ids = []

    def _persist(self):
        faiss.write_index(self._index, self.index_path)
        np.save(self.index_path + ".meta.npy", np.array(self._ids, dtype=object), allow_pickle=True)

    # PUBLIC_INTERFACE
    def add_text_chunks(self, document_id: int, chunks: List[str], vector_dim: int | None = None):
        """Add chunks for a document to the FAISS index."""
        vectors = np.array(embed_texts(chunks), dtype='float32')
        if vector_dim is not None:
            self.dim = vector_dim
        self._index.add(vectors)
        start = len(self._ids)
        for i in range(len(chunks)):
            self._ids.append((document_id, i))
        self._persist()
        return list(range(start, start + len(chunks)))

    # PUBLIC_INTERFACE
    def search(self, query: str, top_k: int = 5) -> List[Tuple[float, Tuple[int, int]]]:
        """Search the FAISS index returning list of (score, (document_id, chunk_index))."""
        if self._index.ntotal == 0:
            return []
        vec = np.array(embed_texts([query]), dtype='float32')
        scores, idxs = self._index.search(vec, top_k)
        results: List[Tuple[float, Tuple[int, int]]] = []
        for score, idx in zip(scores[0].tolist(), idxs[0].tolist()):
            if idx < 0 or idx >= len(self._ids):
                continue
            results.append((float(score), self._ids[idx]))
        return results
