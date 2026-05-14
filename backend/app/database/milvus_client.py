from pymilvus import (
    connections, Collection, CollectionSchema,
    FieldSchema, DataType, utility,
)
from typing import Any


class MilvusClient:
    def __init__(self, host: str = "localhost", port: int = 19530, dim: int = 1024):
        self.host = host
        self.port = port
        self.dim = dim
        connections.connect("default", host=host, port=port)

    def _build_schema_fields(self) -> list[FieldSchema]:
        return [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=8192),
            FieldSchema(name="entity_name", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
        ]

    def create_collection(self, name: str) -> None:
        schema = CollectionSchema(self._build_schema_fields())
        col = Collection(name, schema)
        col.create_index(
            field_name="embedding",
            index_params={"metric_type": "COSINE", "index_type": "IVF_FLAT", "params": {"nlist": 128}},
        )

    def insert(self, collection: str, data: list[dict[str, Any]]) -> int:
        col = Collection(collection)
        # data: [{text, entity_name, source, embedding}]
        texts = [d["text"] for d in data]
        entities = [d["entity_name"] for d in data]
        sources = [d.get("source", "") for d in data]
        embeddings = [d["embedding"] for d in data]
        mr = col.insert([texts, entities, sources, embeddings])
        col.flush()
        return mr.insert_count

    def search(self, collection: str, vector: list[float], top_k: int = 10) -> list[dict]:
        col = Collection(collection)
        col.load()
        results = col.search(
            data=[vector],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"nprobe": 16}},
            limit=top_k,
            output_fields=["text", "entity_name", "source"],
        )
        output = []
        for hit in results[0]:
            output.append({
                "id": hit.id,
                "text": hit.entity.get("text", ""),
                "entity_name": hit.entity.get("entity_name", ""),
                "source": hit.entity.get("source", ""),
                "score": hit.score,
            })
        return output

    def has_collection(self, name: str) -> bool:
        return utility.has_collection(name)

    def drop_collection(self, name: str) -> None:
        col = Collection(name)
        col.drop()

    def count(self, collection: str) -> int:
        col = Collection(collection)
        return col.num_entities

    def load_all_docs(self, collection: str) -> list[dict]:
        """Load all documents from collection for BM25 index."""
        col = Collection(collection)
        col.load()
        results = col.query(
            expr="id >= 0",
            output_fields=["id", "text", "entity_name", "source"],
            limit=10000,
        )
        return [
            {
                "id": r["id"],
                "text": r["text"],
                "entity_name": r["entity_name"],
                "source": r["source"],
            }
            for r in results
        ]
