import pytest
from backend.app.database.neo4j_client import Neo4jClient
from backend.app.data.parser import Triple
from backend.app.data.importer import GraphImporter


@pytest.fixture
async def neo4j_client():
    client = Neo4jClient(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="test_password",
    )
    await client.connect()
    yield client
    await client.close()


@pytest.fixture
def importer(neo4j_client: Neo4jClient):
    return GraphImporter(neo4j_client)


async def test_import_triples(neo4j_client: Neo4jClient, importer: GraphImporter):
    test_entity = "__TEST_APPLE__"
    triples = [
        Triple(entity=test_entity, attribute="描述", value="一种水果", relation_type="DESCRIPTION"),
        Triple(entity=test_entity, attribute="标签", value="食品", relation_type="TAG"),
    ]

    # Import
    count = await importer.import_triples(triples, source="test_source")
    assert count >= 1  # at least the entity was created

    # Verify in Neo4j
    result = await neo4j_client.execute(
        "MATCH (e:Entity {name: $name, source: $source}) RETURN e",
        name=test_entity,
        source="test_source",
    )
    assert len(result) == 1
    node = result[0]["e"]
    assert node["name"] == test_entity
    assert node["描述"] == "一种水果"
    assert node["标签"] == "食品"

    # Cleanup
    await neo4j_client.execute(
        "MATCH (e:Entity {name: $name, source: $source}) DETACH DELETE e",
        name=test_entity,
        source="test_source",
    )


async def test_import_empty_list(importer: GraphImporter):
    count = await importer.import_triples([], source="test")
    assert count == 0
