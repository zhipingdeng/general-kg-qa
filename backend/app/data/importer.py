from app.database.neo4j_client import Neo4jClient
from app.data.parser import Triple


class GraphImporter:
    BATCH_SIZE = 500

    def __init__(self, client: Neo4jClient):
        self._client = client

    async def import_triples(self, triples: list[Triple], source: str = "ownthink") -> int:
        if not triples:
            return 0

        await self._client.execute(
            "CREATE INDEX entity_name IF NOT EXISTS FOR (n:Entity) ON (n.name)"
        )
        count = 0
        batch = []
        for t in triples:
            batch.append(
                {
                    "entity": t.entity,
                    "attr": t.attribute,
                    "value": t.value,
                    "rel_type": t.relation_type,
                    "source": source,
                }
            )
            if len(batch) >= self.BATCH_SIZE:
                count += await self._import_batch(batch)
                batch = []
        if batch:
            count += await self._import_batch(batch)
        return count

    async def _import_batch(self, batch: list[dict]) -> int:
        query = """
        UNWIND $batch AS row
        MERGE (e:Entity {name: row.entity, source: row.source})
        SET e[row.attr] = row.value
        RETURN count(e) AS cnt
        """
        result = await self._client.execute(query, batch=batch)
        return result[0]["cnt"] if result else 0

    async def create_tag_relationships(self, source: str = "ownthink") -> int:
        """Create TAG relationships: Entity -[:TAG]-> TagCategory nodes."""
        # 1. Create TagCategory nodes from entity tags
        await self._client.execute("""
            MATCH (e:Entity {source: $source})
            WHERE e.标签 IS NOT NULL AND e.标签 <> ''
            WITH DISTINCT e.标签 AS tag
            MERGE (t:TagCategory {name: tag})
            RETURN count(t) AS cnt
        """, source=source)

        # 2. Create TAG relationships
        result = await self._client.execute("""
            MATCH (e:Entity {source: $source})
            WHERE e.标签 IS NOT NULL AND e.标签 <> ''
            MATCH (t:TagCategory {name: e.标签})
            MERGE (e)-[:TAG]->(t)
            RETURN count(*) AS cnt
        """, source=source)
        return result[0]["cnt"] if result else 0

    async def create_attribute_relationships(self, source: str = "ownthink") -> int:
        """Create relationships where attribute values match other entity names."""
        # Find entities whose attribute values match other entity names
        result = await self._client.execute("""
            MATCH (e1:Entity {source: $source})
            WHERE e1.所属城市 IS NOT NULL
            MATCH (e2:Entity {name: e1.所属城市, source: $source})
            MERGE (e1)-[:LOCATED_IN]->(e2)
            RETURN count(*) AS cnt
        """, source=source)
        count = result[0]["cnt"] if result else 0

        result2 = await self._client.execute("""
            MATCH (e1:Entity {source: $source})
            WHERE e1.所属地区 IS NOT NULL
            MATCH (e2:Entity {name: e1.所属地区, source: $source})
            MERGE (e1)-[:BELONGS_TO]->(e2)
            RETURN count(*) AS cnt
        """, source=source)
        count += result2[0]["cnt"] if result2 else 0

        return count
