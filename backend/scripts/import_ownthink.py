"""Import OwnThink KG triples into Neo4j (sample 100k)."""
import asyncio
import csv
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings
from app.database.neo4j_client import Neo4jClient
from app.data.parser import OwnThinkParser
from app.data.importer import GraphImporter


OWNTHINK_PATH = "/mnt/e/hermes_code_workspace/dataset/通用百科数据集/OwnThink_KG/ownthink_v2.csv"
SAMPLE_LIMIT = 100_000


async def main():
    settings = get_settings()
    client = Neo4jClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    await client.connect()

    parser = OwnThinkParser()
    importer = GraphImporter(client)

    triples = []
    with open(OWNTHINK_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if len(row) < 3:
                continue
            t = parser.parse_line(",".join(row))
            if t:
                triples.append(t)
            if len(triples) >= SAMPLE_LIMIT:
                break

    print(f"Parsed {len(triples)} triples, importing to Neo4j...")
    imported = await importer.import_triples(triples, source="ownthink")
    print(f"Imported {imported} records.")

    result = await client.execute("MATCH (n:Entity {source: 'ownthink'}) RETURN count(n) AS cnt")
    print(f"Neo4j entity count: {result[0]['cnt']}")
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
