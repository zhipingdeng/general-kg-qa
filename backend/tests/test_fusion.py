"""Tests for RRF fusion function."""
from app.rag.fusion import rrf_fusion


def test_rrf_basic():
    """Two lists merge with correct ranking."""
    list_a = [
        {"id": 1, "entity_name": "A", "text": "doc1"},
        {"id": 2, "entity_name": "B", "text": "doc2"},
    ]
    list_b = [
        {"id": 2, "entity_name": "B", "text": "doc2"},
        {"id": 3, "entity_name": "C", "text": "doc3"},
    ]
    result = rrf_fusion([list_a, list_b], top_k=3)
    assert len(result) == 3
    # id=2 appears in both lists, should be ranked first
    assert result[0]["id"] == 2
    assert "rrf_score" in result[0]


def test_rrf_dedup():
    """Same doc in multiple lists gets score accumulation."""
    list_a = [{"id": 1, "entity_name": "X", "text": "x"}]
    list_b = [{"id": 1, "entity_name": "X", "text": "x"}]
    result = rrf_fusion([list_a, list_b], top_k=5)
    assert len(result) == 1
    # Score should be 2 * 1/(60+0+1) = 2/61
    expected = 2 * (1.0 / (60 + 0 + 1))
    assert abs(result[0]["rrf_score"] - expected) < 1e-6


def test_rrf_empty_lists():
    """Empty lists should not crash."""
    result = rrf_fusion([[], []], top_k=5)
    assert result == []


def test_rrf_single_list():
    """Single list passes through with RRF scores."""
    docs = [
        {"id": 1, "entity_name": "A", "text": "a"},
        {"id": 2, "entity_name": "B", "text": "b"},
    ]
    result = rrf_fusion([docs], top_k=2)
    assert len(result) == 2
    assert result[0]["rrf_score"] > result[1]["rrf_score"]


def test_rrf_entity_name_fallback():
    """When id is missing, entity_name is used as doc_id."""
    docs = [
        {"entity_name": "苹果", "text": "fruit"},
        {"entity_name": "香蕉", "text": "fruit2"},
    ]
    result = rrf_fusion([docs], top_k=2)
    assert len(result) == 2
