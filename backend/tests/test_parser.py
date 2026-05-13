import pytest
from backend.app.data.parser import OwnThinkParser, Triple


@pytest.fixture
def parser():
    return OwnThinkParser()


class TestParseLine:
    def test_parse_valid_line(self, parser: OwnThinkParser):
        line = "胶饴,描述,别名: 饴糖、畅糖、畅、软糖。"
        t = parser.parse_line(line)
        assert t is not None
        assert t.entity == "胶饴"
        assert t.attribute == "描述"
        assert t.value == "别名: 饴糖、畅糖、畅、软糖。"
        assert t.relation_type == "DESCRIPTION"

    def test_parse_empty_line_returns_none(self, parser: OwnThinkParser):
        assert parser.parse_line("") is None
        assert parser.parse_line("   ") is None

    def test_parse_malformed_line_returns_none(self, parser: OwnThinkParser):
        assert parser.parse_line("only,two") is None
        assert parser.parse_line(",,,") is None
        assert parser.parse_line(",attr,val") is None
        assert parser.parse_line("entity,,val") is None

    def test_parse_line_strips_whitespace(self, parser: OwnThinkParser):
        line = " 苹果 , 标签 , 食品 "
        t = parser.parse_line(line)
        assert t is not None
        assert t.entity == "苹果"
        assert t.attribute == "标签"
        assert t.value == "食品"


class TestClassifyRelation:
    def test_classify_known_relations(self, parser: OwnThinkParser):
        assert parser.classify_relation("描述") == "DESCRIPTION"
        assert parser.classify_relation("中文名") == "NAME"
        assert parser.classify_relation("标签") == "TAG"
        assert parser.classify_relation("外文名") == "FOREIGN_NAME"
        assert parser.classify_relation("别名") == "ALIAS"

    def test_classify_unknown_relation_returns_attribute(self, parser: OwnThinkParser):
        assert parser.classify_relation("出生日期") == "ATTRIBUTE"
        assert parser.classify_relation("国籍") == "ATTRIBUTE"
        assert parser.classify_relation("") == "ATTRIBUTE"
