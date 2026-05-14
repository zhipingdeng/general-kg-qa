"""QA Pipeline - Hybrid retrieval + LLM answer generation."""
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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class QAPipeline:
    def __init__(self, retriever: HybridRetriever, generator: AnswerGenerator):
        self.retriever = retriever
        self.generator = generator

    async def answer(self, question: str) -> QAResult:
        # 1. Hybrid retrieval
        docs = await self.retriever.retrieve(question, top_k=5)

        # 2. Build context from retrieved documents
        context_parts = []
        for i, doc in enumerate(docs, 1):
            entity = doc.get("entity_name", "")
            text = doc.get("text", "")
            score = doc.get("rrf_score", 0)
            context_parts.append(f"[{i}] {entity}: {text} (相关度: {score:.3f})")
        context = "\n".join(context_parts)

        # 3. LLM generate answer with context
        answer = await self.generator.generate_with_context(question, context)

        return QAResult(
            question=question,
            entities=[d.get("entity_name", "") for d in docs[:3]],
            answer=answer,
            sources=docs,
        )
