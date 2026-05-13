import pytest
from backend.app.qa.entity_linker import EntityLinker


def test_extract_entity_from_question():
    """Mock entities includes 苹果/香蕉/苹果公司; question contains 苹果 -> should match 苹果."""
    linker = EntityLinker(mock_entities=["苹果", "香蕉", "苹果公司"])
    result = linker.extract_entities("苹果的产地是哪里？")
    assert result == ["苹果"]


def test_longest_match_first():
    """When both 苹果 and 苹果公司 match, 苹果公司 (longer) should win."""
    linker = EntityLinker(mock_entities=["苹果", "苹果公司"])
    result = linker.extract_entities("苹果公司的创始人是谁？")
    assert result == ["苹果公司"]


def test_no_match_returns_empty():
    linker = EntityLinker(mock_entities=["苹果", "香蕉"])
    result = linker.extract_entities("今天天气怎么样？")
    assert result == []


def test_multiple_entities_in_question():
    linker = EntityLinker(mock_entities=["苹果", "香蕉", "橘子"])
    result = linker.extract_entities("苹果和香蕉哪个更好吃？")
    assert "苹果" in result
    assert "香蕉" in result
    assert len(result) == 2


def test_load_from_neo4j():
    linker = EntityLinker()
    linker.load_from_neo4j(["苹果", "香蕉"])
    result = linker.extract_entities("苹果好吃吗？")
    assert result == ["苹果"]
