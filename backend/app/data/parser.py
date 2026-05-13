from dataclasses import dataclass
from typing import Optional


@dataclass
class Triple:
    entity: str
    attribute: str
    value: str
    relation_type: str = "ATTRIBUTE"


class OwnThinkParser:
    RELATION_MAP = {
        "描述": "DESCRIPTION",
        "中文名": "NAME",
        "标签": "TAG",
        "外文名": "FOREIGN_NAME",
        "别名": "ALIAS",
    }

    def parse_line(self, line: str) -> Optional[Triple]:
        line = line.strip().rstrip("\r")
        if not line:
            return None
        parts = line.split(",", 2)
        if len(parts) < 3:
            return None
        entity, attr, value = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if not entity or not attr or not value:
            return None
        return Triple(
            entity=entity,
            attribute=attr,
            value=value,
            relation_type=self.classify_relation(attr),
        )

    def classify_relation(self, attribute: str) -> str:
        return self.RELATION_MAP.get(attribute, "ATTRIBUTE")
