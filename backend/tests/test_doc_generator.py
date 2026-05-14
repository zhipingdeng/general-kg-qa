"""Tests for DocGenerator - TDD: write tests first."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.rag.doc_generator import DocGenerator


@pytest.fixture
def gen():
    return DocGenerator()


class TestEntityToDocument:
    def test_basic_entity_with_properties(self, gen):
        """实体+属性生成自然语言文档"""
        doc = gen.entity_to_document(
            entity="Python",
            properties={"type": "编程语言", "creator": "Guido"},
            relationships=[],
        )
        assert "Python" in doc
        assert "编程语言" in doc
        assert "Guido" in doc
        assert doc.endswith("。")

    def test_entity_with_relationships(self, gen):
        """实体+关系生成文档"""
        doc = gen.entity_to_document(
            entity="Python",
            properties={"type": "编程语言"},
            relationships=[
                {"relation": "创建者", "target": "Guido van Rossum"},
            ],
        )
        assert "Python" in doc
        assert "Guido van Rossum" in doc
        assert "创建者" in doc

    def test_skip_name_and_source_keys(self, gen):
        """name 和 source 属性应被跳过"""
        doc = gen.entity_to_document(
            entity="Test",
            properties={"name": "Test", "source": "wiki", "desc": "测试"},
            relationships=[],
        )
        # name/source values should NOT appear as "Test的name是Test"
        assert "Test的name" not in doc
        assert "source" not in doc or "Test的source" not in doc
        assert "测试" in doc

    def test_empty_properties_no_crash(self, gen):
        """空属性不崩溃"""
        doc = gen.entity_to_document("Empty", {}, [])
        assert "Empty" in doc
        assert doc.endswith("。")

    def test_none_property_values_skipped(self, gen):
        """None 属性值应被跳过"""
        doc = gen.entity_to_document(
            entity="NullTest",
            properties={"good": "ok", "bad": None},
            relationships=[],
        )
        assert "ok" in doc
        assert "None" not in doc


class TestEntitiesToDocuments:
    def test_batch_generation(self, gen):
        """批量生成文档"""
        entities = [
            {"name": "A", "properties": {"x": "1"}, "relationships": []},
            {"name": "B", "properties": {}, "relationships": [
                {"relation": "likes", "target": "A"},
            ]},
        ]
        docs = gen.entities_to_documents(entities)
        assert len(docs) == 2
        assert docs[0]["entity_name"] == "A"
        assert docs[0]["source"] == "neo4j"
        assert docs[1]["entity_name"] == "B"
        assert "likes" in docs[1]["text"]

    def test_empty_list(self, gen):
        """空列表返回空"""
        docs = gen.entities_to_documents([])
        assert docs == []

    def test_minimal_entity(self, gen):
        """只传 name，无 properties/relationships"""
        docs = gen.entities_to_documents([{"name": "X"}])
        assert len(docs) == 1
        assert "X" in docs[0]["text"]
