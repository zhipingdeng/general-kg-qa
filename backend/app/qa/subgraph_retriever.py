"""Subgraph Retriever - Query Neo4j for entity properties and relationships."""

from app.database.neo4j_client import Neo4jClient
from typing import Any


class SubgraphRetriever:
    def __init__(self, client: Neo4jClient):
        self._client = client

    async def retrieve(self, entity_name: str, source: str | None = None) -> dict[str, Any]:
        """Retrieve entity properties and outgoing relationships from Neo4j.

        Args:
            entity_name: The name of the entity to look up.
            source: Optional source filter (e.g. 'wiki', 'ownthink').

        Returns:
            Dict with keys: entity, properties, relationships.
        """
        where = "n.name = $name"
        params: dict[str, Any] = {"name": entity_name}
        if source:
            where += " AND n.source = $source"
            params["source"] = source

        # Query 1: Get entity properties
        props_query = f"MATCH (n:Entity WHERE {where}) RETURN properties(n) AS props"
        props_result = await self._client.execute(props_query, **params)

        properties = {}
        if props_result:
            properties = {
                k: v
                for k, v in props_result[0]["props"].items()
                if k not in ("name", "source")
            }

        # Query 2: Get outgoing relationships
        rel_query = f"""
        MATCH (n:Entity WHERE {where})-[r]->(m:Entity)
        RETURN type(r) AS rel_type, m.name AS target, properties(r) AS rel_props
        LIMIT 50
        """
        rel_result = await self._client.execute(rel_query, **params)

        relationships = []
        for row in rel_result:
            relationships.append({
                "relation": row["rel_type"],
                "target": row["target"],
                "properties": row["rel_props"],
            })

        return {
            "entity": entity_name,
            "properties": properties,
            "relationships": relationships,
        }
