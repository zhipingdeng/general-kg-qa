import pytest
from backend.app.qa.answer_generator import AnswerGenerator


def test_build_prompt_contains_entity():
    """Prompt should contain the entity name."""
    gen = AnswerGenerator(model_name="test", base_url="http://test", api_key="test")
    subgraph = {
        "entity": "苹果",
        "properties": {"描述": "一种水果"},
        "relationships": [],
    }
    prompt = gen.build_prompt("苹果是什么？", subgraph)
    assert "苹果" in prompt
    assert "一种水果" in prompt


def test_build_prompt_contains_question():
    """Prompt should contain the original question."""
    gen = AnswerGenerator(model_name="test", base_url="http://test", api_key="test")
    subgraph = {
        "entity": "苹果",
        "properties": {},
        "relationships": [],
    }
    prompt = gen.build_prompt("苹果的产地是哪里？", subgraph)
    assert "苹果的产地是哪里？" in prompt


def test_build_prompt_with_relationships():
    """Prompt should contain relationship information."""
    gen = AnswerGenerator(model_name="test", base_url="http://test", api_key="test")
    subgraph = {
        "entity": "苹果",
        "properties": {"描述": "一种水果"},
        "relationships": [
            {"relation": "属于", "target": "水果", "properties": {}},
            {"relation": "产自", "target": "中国", "properties": {"比例": "80%"}},
        ],
    }
    prompt = gen.build_prompt("苹果属于什么？", subgraph)
    assert "属于" in prompt
    assert "水果" in prompt
    assert "产自" in prompt
    assert "中国" in prompt


def test_build_prompt_empty_subgraph():
    """Prompt should handle empty properties and relationships."""
    gen = AnswerGenerator(model_name="test", base_url="http://test", api_key="test")
    subgraph = {
        "entity": "未知实体",
        "properties": {},
        "relationships": [],
    }
    prompt = gen.build_prompt("这是什么？", subgraph)
    assert "未知实体" in prompt
    assert "这是什么？" in prompt


def test_build_prompt_multiple_properties():
    """Prompt should contain all properties."""
    gen = AnswerGenerator(model_name="test", base_url="http://test", api_key="test")
    subgraph = {
        "entity": "苹果",
        "properties": {"描述": "一种水果", "颜色": "红色", "产地": "中国"},
        "relationships": [],
    }
    prompt = gen.build_prompt("苹果的描述是什么？", subgraph)
    assert "描述" in prompt
    assert "一种水果" in prompt
    assert "颜色" in prompt
    assert "红色" in prompt
    assert "产地" in prompt
    assert "中国" in prompt
