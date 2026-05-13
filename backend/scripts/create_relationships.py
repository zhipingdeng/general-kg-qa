"""Create relationships between entities after initial import."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import get_settings
from app.database.neo4j_client import Neo4jClient
from app.data.importer import GraphImporter


async def main():
    settings = get_settings()
    client = Neo4jClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    await client.connect()
    importer = GraphImporter(client)

    print("Creating TAG relationships...")
    tag_count = await importer.create_tag_relationships("ownthink")
    print(f"  Created {tag_count} TAG relationships")

    print("Creating attribute relationships...")
    attr_count = await importer.create_attribute_relationships("ownthink")
    print(f"  Created {attr_count} attribute relationships")

    # Summary
    result = await client.execute("MATCH ()-[r]->() RETURN type(r) AS t, count(*) AS cnt ORDER BY cnt DESC")
    print("\nRelationship summary:")
    for row in result:
        print(f"  {row['t']}: {row['cnt']}")

    total = await client.execute("MATCH (n) RETURN count(n) AS cnt")
    print(f"\nTotal nodes: {total[0]['cnt']}")
    rel_total = await client.execute("MATCH ()-[r]->() RETURN count(r) AS cnt")
    print(f"Total relationships: {rel_total[0]['cnt']}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
