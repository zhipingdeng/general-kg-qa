"""Document generator: convert Neo4j entities to natural language documents for RAG."""


class DocGenerator:
    def entity_to_document(self, entity: str, properties: dict, relationships: list) -> str:
        """将实体属性+关系转为自然语言文档。"""
        parts = [f"{entity}"]
        for k, v in properties.items():
            if v and k not in ("name", "source"):
                parts.append(f"{entity}的{k}是{v}")
        for r in relationships:
            parts.append(f"{entity}与{r['target']}有{r['relation']}关系")
        return "。".join(parts) + "。"

    def entities_to_documents(self, entities: list[dict]) -> list[dict]:
        """批量生成文档。entities: [{name, properties, relationships}]
        返回: [{text, entity_name, source}]"""
        docs = []
        for e in entities:
            text = self.entity_to_document(
                e["name"],
                e.get("properties", {}),
                e.get("relationships", []),
            )
            docs.append({"text": text, "entity_name": e["name"], "source": "neo4j"})
        return docs
