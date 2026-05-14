import pytest
from unittest.mock import MagicMock, patch
from pymilvus import DataType
from app.database.milvus_client import MilvusClient


def test_create_collection():
    """Test collection creation with correct schema."""
    client = MilvusClient.__new__(MilvusClient)
    client.host = "localhost"
    client.port = 19530
    client.dim = 1024
    # Test that create_collection builds correct schema
    from pymilvus import CollectionSchema, FieldSchema, DataType
    fields = client._build_schema_fields()
    assert len(fields) >= 3  # id, text, embedding
    field_names = [f.name for f in fields]
    assert "id" in field_names
    assert "text" in field_names
    assert "embedding" in field_names


def test_build_schema_fields():
    client = MilvusClient.__new__(MilvusClient)
    client.dim = 1024
    fields = client._build_schema_fields()
    # Find embedding field
    emb_field = [f for f in fields if f.name == "embedding"][0]
    assert emb_field.dtype == DataType.FLOAT_VECTOR
    assert emb_field.params["dim"] == 1024
