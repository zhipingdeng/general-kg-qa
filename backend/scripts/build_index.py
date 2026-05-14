"""Build Milvus vector index from Neo4j entities."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import get_settings
from app.database.neo4j_client import Neo4jClient
from app.database.milvus_client import MilvusClient
from app.rag.embeddings import EmbeddingService
from app.rag.doc_generator import DocGenerator

BATCH_SIZE = 50


async def main():
    settings = get_settings()

    # Neo4j
    neo4j = Neo4jClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    await neo4j.connect()

    # Milvus
    milvus = MilvusClient(host=settings.milvus_host, port=settings.milvus_port, dim=1024)
    collection = settings.milvus_collection
    if not milvus.has_collection(collection):
        milvus.create_collection(collection)
        print(f"Created collection: {collection}")

    # Embedding
    emb = EmbeddingService(base_url=settings.embedding_base_url, model=settings.embedding_model)
    doc_gen = DocGenerator()

    # Read entities from Neo4j
    result = await neo4j.execute("""
        MATCH (e:Entity {source: 'ownthink'})
        OPTIONAL MATCH (e)-[r]->(m)
        RETURN e.name AS name, properties(e) AS props,
               collect({relation: type(r), target: m.name}) AS rels
    """)

    entities = []
    for row in result:
        props = {k: v for k, v in row["props"].items() if k not in ("name", "source")}
        rels = [r for r in row["rels"] if r["target"] is not None]
        entities.append({"name": row["name"], "properties": props, "relationships": rels})

    print(f"Loaded {len(entities)} entities from Neo4j")

    # Generate documents
    docs = doc_gen.entities_to_documents(entities)
    print(f"Generated {len(docs)} documents")

    # Embed and insert in batches
    total_inserted = 0
    for i in range(0, len(docs), BATCH_SIZE):
        batch = docs[i : i + BATCH_SIZE]
        texts = [d["text"] for d in batch]
        vectors = await emb.embed_batch(texts)
        for d, v in zip(batch, vectors):
            d["embedding"] = v
        count = milvus.insert(collection, batch)
        total_inserted += count
        print(f"  Batch {i // BATCH_SIZE + 1}: inserted {count} (total: {total_inserted})")

    print(f"\nDone! Total documents in Milvus: {milvus.count(collection)}")
    await neo4j.close()


if __name__ == "__main__":
    asyncio.run(main())
