from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.app.config import get_settings
from backend.app.database.neo4j_client import Neo4jClient
from backend.app.database.mysql import get_engine, Base
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.qa import router as qa_router
from backend.app.qa.entity_linker import EntityLinker
from backend.app.qa.subgraph_retriever import SubgraphRetriever
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

    # QA Pipeline
    entity_linker = EntityLinker()
    # Load known entities from Neo4j
    try:
        result = await neo4j.execute("MATCH (n:Entity) RETURN n.name AS name LIMIT 10000")
        entity_names = [r["name"] for r in result if r.get("name")]
        entity_linker.load_from_neo4j(entity_names)
    except Exception:
        pass

    subgraph_retriever = SubgraphRetriever(neo4j)
    answer_generator = AnswerGenerator(
        model_name=settings.llm_model_name,
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
    )
    app.state.qa_pipeline = QAPipeline(entity_linker, subgraph_retriever, answer_generator)

    yield

    await neo4j.close()


app = FastAPI(title="General KG-QA", version="0.1.0", lifespan=lifespan)
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
app.include_router(qa_router, prefix="/api/v1", tags=["qa"])
