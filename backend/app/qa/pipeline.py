"""QA Pipeline - Hybrid retrieval with graph, vector, and BM25."""

from dataclasses import dataclass, asdict
from typing import Any
from app.rag.hybrid_retriever import HybridRetriever
from app.qa.answer_generator import AnswerGenerator


@dataclass
class QAResult:
    question: str
    entities: list[str]
    answer: str
    sources: list[dict]
    rewritten_queries: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class QAPipeline:
    def __init__(self, retriever: HybridRetriever, generator: AnswerGenerator):
        self.retriever = retriever
        self.generator = generator

    async def answer(self, question: str) -> QAResult:
        # 1. Hybrid retrieval
        retrieval = await self.retriever.retrieve(question, top_k=5)

        # 2. Build context from fused results + graph
        context_parts = []
        sources = []

        # Fused document results
        for i, doc in enumerate(retrieval["fused_results"][:5], 1):
            entity = doc.get("entity_name", "")
            text = doc.get("text", "")
            score = doc.get("rrf_score", 0)
            context_parts.append(f"[{i}] {entity}: {text} (相关度: {score:.3f})")
            if entity:
                sources.append({"entity_name": entity, "text": text})

        # Graph structured knowledge
        graph = retrieval.get("graph_results", {})
        if graph.get("subgraphs"):
            for sg in graph["subgraphs"]:
                entity = sg.get("entity", "")
                props = sg.get("properties", {})
                rels = sg.get("relationships", [])
                context_parts.append(f"\n[知识图谱] {entity}")
                for k, v in props.items():
                    context_parts.append(f"  {k}: {v}")
                for r in rels[:5]:
                    context_parts.append(f"  {entity} --[{r['relation']}]--> {r['target']}")

        context = "\n".join(context_parts)

        # 3. LLM generate answer with context
        answer = await self.generator.generate_with_context(question, context)

        return QAResult(
            question=question,
            entities=graph.get("entities", []),
            answer=answer,
            sources=sources,
            rewritten_queries=retrieval.get("rewritten_queries", []),
        )
