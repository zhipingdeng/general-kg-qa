"""QA Pipeline - Orchestrate entity linking, subgraph retrieval, and answer generation."""

from dataclasses import dataclass, asdict
from typing import Any
from app.qa.entity_linker import EntityLinker
from app.qa.subgraph_retriever import SubgraphRetriever
from app.qa.answer_generator import AnswerGenerator


@dataclass
class QAResult:
    question: str
    entities: list[str]
    subgraph: dict[str, Any]
    answer: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class QAPipeline:
    def __init__(
        self,
        entity_linker: EntityLinker,
        subgraph_retriever: SubgraphRetriever,
        answer_generator: AnswerGenerator,
    ):
        self.entity_linker = entity_linker
        self.subgraph_retriever = subgraph_retriever
        self.answer_generator = answer_generator

    async def answer(self, question: str) -> QAResult:
        """Process a question through the full QA pipeline.

        Steps:
        1. Extract entities from the question.
        2. If no entities found, return a fallback answer.
        3. Retrieve subgraph for the first (most relevant) entity.
        4. Generate an answer using the LLM.

        Args:
            question: The user's natural language question.

        Returns:
            A QAResult with question, entities, subgraph, and answer.
        """
        entities = self.entity_linker.extract_entities(question)
        if not entities:
            return QAResult(
                question=question,
                entities=[],
                subgraph={},
                answer="抱歉，未能从问题中识别出已知实体。请尝试换一种问法。",
            )

        entity = entities[0]
        subgraph = await self.subgraph_retriever.retrieve(entity)
        answer = await self.answer_generator.generate(question, subgraph)

        return QAResult(
            question=question,
            entities=entities,
            subgraph=subgraph,
            answer=answer,
        )
