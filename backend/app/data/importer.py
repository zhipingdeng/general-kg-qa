from backend.app.database.neo4j_client import Neo4jClient
from backend.app.data.parser import Triple


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
