"""Subgraph Retriever - Query Neo4j for entity properties and relationships."""

import asyncio
from app.database.neo4j_client import Neo4jClient
from typing import Any


class SubgraphRetriever:
    def __init__(self, client: Neo4jClient):
        self._client = client

    async def retrieve(self, entity_name: str, source: str | None = None) -> dict[str, Any]:
        """Retrieve entity properties and outgoing relationships from Neo4j.

        Properties and relationships are fetched concurrently via asyncio.gather.

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

        # Two independent queries — run concurrently
        props_query = f"MATCH (n:Entity WHERE {where}) RETURN properties(n) AS props"
        rel_query = f"""
        MATCH (n:Entity WHERE {where})-[r]->(m)
        RETURN type(r) AS rel_type, labels(m) AS target_labels,
               m.name AS target, properties(r) AS rel_props
        LIMIT 50
        """

        props_result, rel_result = await asyncio.gather(
            self._client.execute(props_query, **params),
            self._client.execute(rel_query, **params),
        )

        properties = {}
        if props_result:
            properties = {
                k: v
                for k, v in props_result[0]["props"].items()
                if k not in ("name", "source")
            }

        relationships = []
        for row in rel_result:
            relationships.append({
                "relation": row["rel_type"],
                "target": row["target"],
                "target_type": row.get("target_labels", [""])[0] if row.get("target_labels") else "",
                "properties": row["rel_props"],
            })

        return {
            "entity": entity_name,
            "properties": properties,
            "relationships": relationships,
        }
