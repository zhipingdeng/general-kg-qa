"""Check Neo4j entity count for a project."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.database.neo4j_client import Neo4jClient

async def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "7687"
    name = sys.argv[2] if len(sys.argv) > 2 else "unknown"
    client = Neo4jClient(f"bolt://localhost:{port}", "neo4j", "kgqa123456")
    await client.connect()
    result = await client.execute("MATCH (n:Entity {source: 'ownthink'}) RETURN count(n) AS cnt")
    print(f"{name} (port {port}): {result[0]['cnt']} entities")
    await client.close()

asyncio.run(main())
