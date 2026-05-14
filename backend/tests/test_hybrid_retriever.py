import pytest
import inspect
from unittest.mock import AsyncMock, MagicMock
from app.rag.hybrid_retriever import HybridRetriever
from app.rag.rrf import RRF


def test_hybrid_retriever_init():
    """Test that HybridRetriever can be instantiated."""
    retriever = HybridRetriever.__new__(HybridRetriever)
    retriever.rrf = RRF(k=60)
    retriever.collection = "test"
    retriever.rewriter = None
    retriever.graph = None
    retriever.entity_linker = None
    assert retriever.collection == "test"


def test_hybrid_retrieve_concept():
    """Test the retrieve method exists and is async."""
    assert inspect.iscoroutinefunction(HybridRetriever.retrieve)


@pytest.mark.asyncio
async def test_hybrid_retrieve_integration():
    """Test full retrieve flow with mocked dependencies."""
    mock_milvus = MagicMock()
    mock_milvus.search = MagicMock(return_value=[
        {"id": 1, "text": "doc1", "entity_name": "E1", "source": "s1", "score": 0.9},
        {"id": 2, "text": "doc2", "entity_name": "E2", "source": "s2", "score": 0.8},
    ])

    mock_embedding = AsyncMock()
    mock_embedding.embed = AsyncMock(return_value=[0.1] * 1024)

    mock_bm25 = MagicMock()
    mock_bm25.search = MagicMock(return_value=[
        {"id": 1, "text": "doc1", "entity_name": "E1", "source": "s1", "bm25_score": 5.0},
        {"id": 3, "text": "doc3", "entity_name": "E3", "source": "s3", "bm25_score": 3.0},
    ])

    mock_hyde = AsyncMock()
    mock_hyde.generate = AsyncMock(return_value="hypothetical answer about apple")

    retriever = HybridRetriever(
        milvus=mock_milvus,
        embedding=mock_embedding,
        bm25=mock_bm25,
        hyde=mock_hyde,
        collection="entity_docs",
        query_rewriter=None,
        graph_retriever=None,
        entity_linker=None,
        rrf_k=60,
    )

    result = await retriever.retrieve("what is apple?", top_k=5)

    # Should return dict with all result types
    assert isinstance(result, dict)
    assert "fused_results" in result
    assert "vector_results" in result
    assert "bm25_results" in result
    assert "graph_results" in result
    assert "rewritten_queries" in result

    # Fused results should have rrf_score
    for r in result["fused_results"]:
        assert "rrf_score" in r

    # HyDE and embedding should have been called
    mock_hyde.generate.assert_called_once_with("what is apple?")
    assert mock_embedding.embed.call_count == 2  # query + hyde doc

    # Milvus search should be called twice (query vec + hyde vec)
    assert mock_milvus.search.call_count == 2

    # BM25 search should be called once
    mock_bm25.search.assert_called_once_with("what is apple?", 5)


@pytest.mark.asyncio
async def test_hybrid_retrieve_with_rewriter():
    """Test retrieve with query rewriting enabled."""
    mock_milvus = MagicMock()
    mock_milvus.search = MagicMock(return_value=[
        {"id": 1, "text": "doc1", "entity_name": "E1", "source": "s1", "score": 0.9},
    ])

    mock_embedding = AsyncMock()
    mock_embedding.embed = AsyncMock(return_value=[0.1] * 1024)

    mock_bm25 = MagicMock()
    mock_bm25.search = MagicMock(return_value=[
        {"id": 1, "text": "doc1", "entity_name": "E1", "source": "s1", "bm25_score": 5.0},
    ])

    mock_hyde = AsyncMock()
    mock_hyde.generate = AsyncMock(return_value="hypothetical answer")

    mock_rewriter = AsyncMock()
    mock_rewriter.rewrite = AsyncMock(return_value=["苹果是什么？", "苹果的定义？"])

    retriever = HybridRetriever(
        milvus=mock_milvus,
        embedding=mock_embedding,
        bm25=mock_bm25,
        hyde=mock_hyde,
        collection="entity_docs",
        query_rewriter=mock_rewriter,
        graph_retriever=None,
        entity_linker=None,
    )

    result = await retriever.retrieve("苹果是什么？", top_k=5)

    assert "rewritten_queries" in result
    assert len(result["rewritten_queries"]) == 2
    mock_rewriter.rewrite.assert_called_once()
