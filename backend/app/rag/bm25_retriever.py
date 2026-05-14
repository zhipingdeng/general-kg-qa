import bm25s
import numpy as np


class BM25Retriever:
    def __init__(self):
        self._docs: list[dict] = []
        self._bm25 = None
        self._tokenized_corpus = None

    def build_index(self, docs: list[dict]) -> None:
        """Build BM25 inverted index from documents.
        docs: [{text, entity_name, id, ...}]
        """
        self._docs = docs
        corpus = [d["text"] for d in docs]
        tokenized = bm25s.tokenize(corpus)
        self._bm25 = bm25s.BM25()
        self._bm25.index(tokenized)
        self._tokenized_corpus = tokenized

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Keyword search, returns docs with bm25_score."""
        if not self._bm25 or not self._docs:
            return []
        query_tokens = bm25s.tokenize(query)
        scores, indices = self._bm25.retrieve(query_tokens, k=min(top_k, len(self._docs)))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            idx = int(idx)
            if idx < 0 or idx >= len(self._docs):
                continue
            doc = self._docs[idx].copy()
            doc["bm25_score"] = float(score)
            results.append(doc)
        return results
