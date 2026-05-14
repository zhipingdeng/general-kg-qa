from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import get_settings
from app.database.neo4j_client import Neo4jClient
from app.database.milvus_client import MilvusClient
from app.database.mysql import get_engine, Base
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.qa import router as qa_router
from app.api.v1.knowledge import router as knowledge_router
from app.rag.embeddings import EmbeddingService
from app.rag.bm25_retriever import BM25Retriever
from app.rag.hyde import HyDEGenerator
from app.rag.query_rewriter import QueryRewriter
from app.rag.hybrid_retriever import HybridRetriever
from app.qa.entity_linker import EntityLinker
from app.qa.subgraph_retriever import SubgraphRetriever
from app.qa.answer_generator import AnswerGenerator
from app.qa.pipeline import QAPipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # MySQL tables
    engine = get_engine(
        host=settings.mysql_host, port=settings.mysql_port,
        user=settings.mysql_user, password=settings.mysql_password,
        database=settings.mysql_database,
    )
    Base.metadata.create_all(bind=engine)

    # Neo4j
    neo4j = Neo4jClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    await neo4j.connect()
    app.state.neo4j = neo4j

    # Milvus
    milvus = MilvusClient(host=settings.milvus_host, port=settings.milvus_port)

    # Embedding
    embedding = EmbeddingService(
        base_url=settings.embedding_base_url,
        model=settings.embedding_model,
    )

    # HyDE
    hyde = HyDEGenerator(
        settings.llm_model_name,
        settings.llm_base_url,
        settings.llm_api_key,
    )

    # BM25: load documents from Milvus collection
    bm25 = BM25Retriever()
    try:
        docs = milvus.load_all_docs(settings.milvus_collection)
        bm25.build_index(docs)
    except Exception:
        pass

    # Query Rewriter
    query_rewriter = QueryRewriter(
        settings.llm_model_name,
        settings.llm_base_url,
        settings.llm_api_key,
    )

    # Entity Linker + Graph Retriever
    entity_linker = EntityLinker()
    graph_retriever = SubgraphRetriever(neo4j)

    # Load known entities for entity linker
    try:
        result = await neo4j.execute(
            "MATCH (n:Entity {source: 'ownthink'}) RETURN n.name AS name LIMIT 5000"
        )
        entity_names = [r["name"] for r in result if r.get("name")]
        entity_linker.load_from_neo4j(entity_names)
    except Exception:
        pass

    # Hybrid Retriever (vector + BM25 + HyDE + graph)
    retriever = HybridRetriever(
        milvus=milvus,
        embedding=embedding,
        bm25=bm25,
        hyde=hyde,
        collection=settings.milvus_collection,
        query_rewriter=query_rewriter,
        graph_retriever=graph_retriever,
        entity_linker=entity_linker,
    )

    # Answer Generator
    generator = AnswerGenerator(
        settings.llm_model_name,
        settings.llm_base_url,
        settings.llm_api_key,
    )

    # Pipeline
    app.state.qa_pipeline = QAPipeline(retriever, generator)

    yield

    await neo4j.close()


app = FastAPI(title="General KG-QA", version="0.1.0", lifespan=lifespan)
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
app.include_router(qa_router, prefix="/api/v1", tags=["qa"])
app.include_router(knowledge_router, prefix="/api/v1", tags=["knowledge"])
