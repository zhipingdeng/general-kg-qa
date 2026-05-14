import pytest
from unittest.mock import AsyncMock, MagicMock
from app.qa.answer_generator import AnswerGenerator
from app.qa.pipeline import QAPipeline, QAResult


def test_qaresult_to_dict():
    """QAResult.to_dict() should return a proper dictionary."""
    result = QAResult(
        question="苹果是什么？",
        entities=["苹果"],
        answer="苹果是一种水果。",
        sources=[{"entity_name": "苹果", "text": "一种水果"}],
        rewritten_queries=["苹果是什么？", "苹果的定义"],
    )
    d = result.to_dict()
    assert d["question"] == "苹果是什么？"
    assert d["entities"] == ["苹果"]
    assert d["answer"] == "苹果是一种水果。"
    assert "sources" in d
    assert "rewritten_queries" in d


@pytest.mark.asyncio
async def test_pipeline_answer_with_mocks():
    """Full pipeline test with mocked retriever and generator."""
    mock_retriever = AsyncMock()
    mock_retriever.retrieve = AsyncMock(return_value={
        "fused_results": [
            {"id": 1, "text": "苹果是一种水果", "entity_name": "苹果", "source": "s1", "rrf_score": 0.05},
            {"id": 2, "text": "苹果原产于中国", "entity_name": "苹果", "source": "s2", "rrf_score": 0.03},
        ],
        "graph_results": {
            "entities": ["苹果"],
            "subgraphs": [{"entity": "苹果", "properties": {"描述": "一种水果"}, "relationships": []}],
        },
        "rewritten_queries": ["苹果是什么？"],
        "vector_results": [],
        "bm25_results": [],
    })

    mock_generator = AsyncMock()
    mock_generator.generate_with_context = AsyncMock(return_value="苹果是一种水果，原产于中国。")

    pipeline = QAPipeline(mock_retriever, mock_generator)
    result = await pipeline.answer("苹果是什么？")

    assert isinstance(result, QAResult)
    assert result.question == "苹果是什么？"
    assert len(result.entities) > 0
    assert "苹果" in result.entities
    assert result.answer == "苹果是一种水果，原产于中国。"
    assert len(result.sources) >= 1
    assert result.rewritten_queries == ["苹果是什么？"]

    # Verify retriever was called correctly
    mock_retriever.retrieve.assert_called_once_with("苹果是什么？", top_k=5)

    # Verify generator was called with context
    mock_generator.generate_with_context.assert_called_once()
    call_args = mock_generator.generate_with_context.call_args
    assert call_args[0][0] == "苹果是什么？"
    assert "苹果" in call_args[0][1]


def test_pipeline_init():
    """Test pipeline initialization."""
    mock_retriever = MagicMock()
    mock_generator = MagicMock()
    pipeline = QAPipeline(mock_retriever, mock_generator)
    assert pipeline.retriever is mock_retriever
    assert pipeline.generator is mock_generator
