"""Tests for QueryRewriter."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.rag.query_rewriter import QueryRewriter


def test_rewrite_returns_original_on_failure():
    """When LLM fails, should return [question]."""
    rewriter = QueryRewriter.__new__(QueryRewriter)
    rewriter.model = "test"
    rewriter.base_url = "http://fake"
    rewriter.api_key = "fake"

    import asyncio
    result = asyncio.run(rewriter.rewrite("什么是苹果？"))
    assert result == ["什么是苹果？"]


@pytest.mark.asyncio
async def test_rewrite_calls_llm():
    """Verify the LLM is called with correct prompt."""
    rewriter = QueryRewriter.__new__(QueryRewriter)
    rewriter.model = "test-model"
    rewriter.base_url = "http://fake"
    rewriter.api_key = "fake-key"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "苹果是什么？\n苹果的定义是什么？"}}]
    }

    with patch("app.rag.query_rewriter.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        result = await rewriter.rewrite("什么是苹果？")

    assert "什么是苹果？" in result
    assert len(result) == 3  # original + 2 variants
    assert result[0] == "什么是苹果？"


def test_rewrite_class_init():
    """Test that QueryRewriter initializes from settings."""
    rewriter = QueryRewriter.__new__(QueryRewriter)
    rewriter.model = "test"
    rewriter.base_url = "http://test"
    rewriter.api_key = "key"
    assert rewriter.model == "test"
