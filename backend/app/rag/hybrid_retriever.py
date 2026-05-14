"""Hybrid Retriever - HyDE + Vector + BM25 with RRF fusion."""
import asyncio
from app.database.milvus_client import MilvusClient
from app.rag.embeddings import EmbeddingService
from app.rag.bm25_retriever import BM25Retriever
from app.rag.hyde import HyDEGenerator
from app.rag.rrf import RRF


class HybridRetriever:
    def __init__(
        self,
        milvus: MilvusClient,
        embedding: EmbeddingService,
        bm25: BM25Retriever,
        hyde: HyDEGenerator,
        collection: str,
        rrf_k: int = 60,
    ):
        self.milvus = milvus
        self.embedding = embedding
        self.bm25 = bm25
        self.hyde = hyde
        self.collection = collection
        self.rrf = RRF(k=rrf_k)

    async def retrieve(self, query: str, top_k: int = 10) -> list[dict]:
        """Three-path retrieval + RRF fusion.

        1. HyDE: generate hypothetical answer + embed query (concurrent)
        2. Concurrent: embed HyDE doc + BM25 search
        3. Concurrent: 2x Milvus vector search
        4. RRF merge
        """
        # Step 1: HyDE + query embedding (concurrent)
        hyde_doc, query_vec = await asyncio.gather(
            self.hyde.generate(query),
            self.embedding.embed(query),
        )

        # Step 2: HyDE embedding + BM25 (concurrent)
        hyde_vec_task = self.embedding.embed(hyde_doc)
        bm25_task = asyncio.to_thread(self.bm25.search, query, top_k)
        hyde_vec, bm25_results = await asyncio.gather(hyde_vec_task, bm25_task)

        # Step 3: Two Milvus searches (concurrent)
        vec_search_task = asyncio.to_thread(
            self.milvus.search, self.collection, query_vec, top_k
        )
        hyde_search_task = asyncio.to_thread(
            self.milvus.search, self.collection, hyde_vec, top_k
        )
        vec_results, hyde_results = await asyncio.gather(
            vec_search_task, hyde_search_task
        )

        # Step 4: RRF fusion
        merged = self.rrf.merge(
            [vec_results, hyde_results, bm25_results], top_k=top_k
        )
        return merged
