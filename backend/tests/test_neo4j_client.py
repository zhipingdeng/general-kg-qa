import pytest
from backend.app.database.neo4j_client import Neo4jClient


@pytest.fixture
async def neo4j_client():
    client = Neo4jClient(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="kgqa123",
    )
    await client.connect()
    yield client
    await client.close()


async def test_connect_and_verify(neo4j_client: Neo4jClient):
    result = await neo4j_client.execute("RETURN 1 AS num")
    assert len(result) == 1
    assert result[0]["num"] == 1


async def test_create_and_read_node(neo4j_client: Neo4jClient):
    # Create a test node
    await neo4j_client.execute(
        "CREATE (n:TestNode {name: $name, value: $value})",
        name="test_item",
        value=42,
    )

    # Read it back
    result = await neo4j_client.execute(
        "MATCH (n:TestNode {name: $name}) RETURN n.name AS name, n.value AS value",
        name="test_item",
    )
    assert len(result) == 1
    assert result[0]["name"] == "test_item"
    assert result[0]["value"] == 42

    # Cleanup
    await neo4j_client.execute(
        "MATCH (n:TestNode {name: $name}) DELETE n",
        name="test_item",
    )
