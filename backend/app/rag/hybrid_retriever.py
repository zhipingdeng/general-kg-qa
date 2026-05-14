"""Hybrid Retriever - combines vector, BM25, graph, and HyDE retrieval with RRF fusion."""

import asyncio
from app.database.milvus_client import MilvusClient
from app.rag.embeddings import EmbeddingService
from app.rag.bm25_retriever import BM25Retriever
from app.rag.hyde import HyDEGenerator
from app.rag.rrf import RRF
from app.rag.query_rewriter import QueryRewriter
from app.qa.subgraph_retriever import SubgraphRetriever
from app.qa.entity_linker import EntityLinker


class HybridRetriever:
    def __init__(
        self,
        milvus: MilvusClient,
        embedding: EmbeddingService,
        bm25: BM25Retriever,
        hyde: HyDEGenerator,
        collection: str,
        query_rewriter: QueryRewriter | None = None,
        graph_retriever: SubgraphRetriever | None = None,
        entity_linker: EntityLinker | None = None,
        rrf_k: int = 60,
    ):
        self.milvus = milvus
        self.embedding = embedding
        self.bm25 = bm25
        self.hyde = hyde
        self.collection = collection
        self.rrf = RRF(k=rrf_k)
        self.rewriter = query_rewriter
        self.graph = graph_retriever
        self.entity_linker = entity_linker

    async def retrieve(self, query: str, top_k: int = 10) -> dict:
        """Four-path retrieval + RRF fusion.

        1. Query rewriting (optional)
        2. HyDE + query embedding (concurrent)
        3. Vector search with query + HyDE + rewritten queries (concurrent)
        4. BM25 search with all query variants (concurrent)
        5. Graph retrieval for entities found in query
        6. RRF merge of vector + BM25 results

        Returns:
            Dict with: vector_results, bm25_results, graph_results, fused_results, rewritten_queries
        """
        # Step 1: Query rewriting
        if self.rewriter:
            queries = await self.rewriter.rewrite(query)
        else:
            queries = [query]

        # Step 2: HyDE + query embedding (concurrent)
        hyde_doc, query_vec = await asyncio.gather(
            self.hyde.generate(query),
            self.embedding.embed(query),
        )

        # Step 3: HyDE embedding + BM25 for main query (concurrent)
        hyde_vec_task = self.embedding.embed(hyde_doc)
        bm25_task = asyncio.to_thread(self.bm25.search, query, top_k)
        hyde_vec, bm25_main = await asyncio.gather(hyde_vec_task, bm25_task)

        # Step 4: Milvus vector searches (concurrent)
        search_tasks = [
            asyncio.to_thread(self.milvus.search, self.collection, query_vec, top_k),
            asyncio.to_thread(self.milvus.search, self.collection, hyde_vec, top_k),
        ]

        # Add searches for rewritten query variants
        for q in queries[1:]:
            q_vec = await self.embedding.embed(q)
            search_tasks.append(
                asyncio.to_thread(self.milvus.search, self.collection, q_vec, top_k)
            )

        vector_results_list = await asyncio.gather(*search_tasks)

        # Step 5: BM25 for rewritten queries
        all_bm25 = [bm25_main]
        for q in queries[1:]:
            all_bm25.append(asyncio.to_thread(self.bm25.search, q, top_k))
        if len(all_bm25) > 1:
            bm25_rest = await asyncio.gather(*all_bm25[1:])
            all_bm25_results = [bm25_main] + list(bm25_rest)
        else:
            all_bm25_results = [bm25_main]

        # Step 6: Graph retrieval
        graph_context = await self._graph_retrieve(query)

        # Step 7: RRF fusion of all vector + BM25 results
        all_lists = list(vector_results_list) + all_bm25_results
        fused = self.rrf.merge(all_lists, top_k=top_k)

        return {
            "vector_results": list(vector_results_list[0])[:5],
            "bm25_results": bm25_main[:5],
            "graph_results": graph_context,
            "fused_results": fused,
            "rewritten_queries": queries,
        }

    async def _graph_retrieve(self, question: str) -> dict:
        """Extract entities from question and retrieve subgraph from Neo4j."""
        if not self.entity_linker or not self.graph:
            return {"entities": [], "subgraphs": []}

        entities = self.entity_linker.extract_entities(question)
        if not entities:
            return {"entities": [], "subgraphs": []}

        # Retrieve subgraph for each found entity (max 3)
        subgraph_tasks = [
            self.graph.retrieve(entity) for entity in entities[:3]
        ]
        subgraphs = await asyncio.gather(*subgraph_tasks, return_exceptions=True)

        valid_subgraphs = []
        for sg in subgraphs:
            if isinstance(sg, dict):
                valid_subgraphs.append(sg)

        return {"entities": entities[:3], "subgraphs": valid_subgraphs}
