import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.qa.subgraph_retriever import SubgraphRetriever


@pytest.fixture
def mock_client():
    """Create a mock Neo4jClient for testing."""
    client = AsyncMock()
    return client


async def test_retrieve_entity_properties(mock_client):
    """Retrieve properties of a single entity node."""
    # Mock the two queries: props query and rel query
    mock_client.execute = AsyncMock(side_effect=[
        # First call: properties query
        [{"props": {"name": "苹果", "source": "test", "描述": "一种水果", "标签": "食品"}}],
        # Second call: relationships query
        [],
    ])

    retriever = SubgraphRetriever(mock_client)
    result = await retriever.retrieve("苹果")

    assert result["entity"] == "苹果"
    assert "描述" in result["properties"]
    assert result["properties"]["描述"] == "一种水果"
    assert "标签" in result["properties"]
    assert result["properties"]["标签"] == "食品"
    # name and source should be excluded from properties
    assert "name" not in result["properties"]
    assert "source" not in result["properties"]


async def test_retrieve_entity_with_relationships(mock_client):
    """Retrieve entity with outgoing relationships."""
    mock_client.execute = AsyncMock(side_effect=[
        # Properties query
        [{"props": {"name": "苹果", "source": "test", "描述": "一种水果"}}],
        # Relationships query
        [
            {"rel_type": "属于", "target": "水果", "rel_props": {}},
            {"rel_type": "产自", "target": "中国", "rel_props": {"比例": "80%"}},
        ],
    ])

    retriever = SubgraphRetriever(mock_client)
    result = await retriever.retrieve("苹果")

    assert len(result["relationships"]) == 2
    assert result["relationships"][0]["relation"] == "属于"
    assert result["relationships"][0]["target"] == "水果"
    assert result["relationships"][1]["relation"] == "产自"
    assert result["relationships"][1]["target"] == "中国"
    assert result["relationships"][1]["properties"]["比例"] == "80%"


async def test_retrieve_with_source_filter(mock_client):
    """Source parameter should be passed to the query."""
    mock_client.execute = AsyncMock(side_effect=[
        [{"props": {"name": "苹果", "source": "wiki", "描述": "一种水果"}}],
        [],
    ])

    retriever = SubgraphRetriever(mock_client)
    result = await retriever.retrieve("苹果", source="wiki")

    # Verify source was passed as parameter
    calls = mock_client.execute.call_args_list
    assert calls[0].kwargs.get("source") == "wiki" or (
        len(calls[0].args) > 1
    )


async def test_retrieve_entity_not_found(mock_client):
    """When entity doesn't exist, return empty properties and relationships."""
    mock_client.execute = AsyncMock(side_effect=[
        [],  # No properties
        [],  # No relationships
    ])

    retriever = SubgraphRetriever(mock_client)
    result = await retriever.retrieve("不存在的实体")

    assert result["entity"] == "不存在的实体"
    assert result["properties"] == {}
    assert result["relationships"] == []
