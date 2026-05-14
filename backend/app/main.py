from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.app.config import get_settings
from backend.app.database.neo4j_client import Neo4jClient
from backend.app.database.milvus_client import MilvusClient
from backend.app.database.mysql import get_engine, Base
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.qa import router as qa_router
from backend.app.api.v1.knowledge import router as knowledge_router
from backend.app.rag.embeddings import EmbeddingService
from backend.app.rag.bm25_retriever import BM25Retriever
from backend.app.rag.hyde import HyDEGenerator
from backend.app.rag.hybrid_retriever import HybridRetriever
from backend.app.qa.answer_generator import AnswerGenerator
from backend.app.qa.pipeline import QAPipeline


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

    # Hybrid Retriever
    retriever = HybridRetriever(
        milvus, embedding, bm25, hyde, settings.milvus_collection,
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
