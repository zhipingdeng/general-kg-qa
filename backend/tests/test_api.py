"""Tests for main app: health and QA endpoints."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from backend.app.database.mysql import Base, get_engine
from backend.app.models.user import User  # ensure User model registered
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.qa import router as qa_router


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test and drop after."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest_asyncio.fixture
async def client():
    """Create a test HTTP client with all routers but no lifespan (no Neo4j/LLM)."""
    test_app = FastAPI()
    test_app.include_router(health_router, prefix="/api/v1")
    test_app.include_router(auth_router, prefix="/api/v1")
    test_app.include_router(qa_router, prefix="/api/v1")
    # Mock qa_pipeline as None (not initialized)
    test_app.state.qa_pipeline = None
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    """Test health endpoint returns ok."""
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["service"] == "general-kg-qa"


@pytest.mark.asyncio
async def test_qa_requires_auth(client):
    """Test that QA endpoint requires authentication."""
    resp = await client.post("/api/v1/qa", json={"question": "苹果的产地？"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_qa_with_auth_no_pipeline(client):
    """Test QA endpoint with valid token but no pipeline initialized."""
    # Register a user first
    reg = await client.post(
        "/api/v1/auth/register",
        json={"username": "qauser", "email": "qa@example.com", "password": "pass123456"},
    )
    assert reg.status_code == 200
    token = reg.json()["access_token"]

    resp = await client.post(
        "/api/v1/qa",
        json={"question": "苹果的产地？"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["question"] == "苹果的产地？"
    assert data["entities"] == []
    assert "未初始化" in data["answer"]


@pytest.mark.asyncio
async def test_qa_with_mock_pipeline(client):
    """Test QA endpoint with a mocked pipeline that returns a result."""
    from backend.app.qa.pipeline import QAResult

    # Create a mock pipeline
    mock_pipeline = AsyncMock()
    mock_pipeline.answer.return_value = QAResult(
        question="苹果的产地？",
        entities=["苹果"],
        subgraph={},
        answer="苹果原产于中亚地区。",
    )

    # Build a test app with the mock pipeline
    test_app = FastAPI()
    test_app.include_router(health_router, prefix="/api/v1")
    test_app.include_router(auth_router, prefix="/api/v1")
    test_app.include_router(qa_router, prefix="/api/v1")
    test_app.state.qa_pipeline = mock_pipeline

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register
        reg = await ac.post(
            "/api/v1/auth/register",
            json={"username": "mockuser", "email": "mock@example.com", "password": "pass123456"},
        )
        token = reg.json()["access_token"]

        resp = await ac.post(
            "/api/v1/qa",
            json={"question": "苹果的产地？"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["question"] == "苹果的产地？"
        assert data["entities"] == ["苹果"]
        assert "苹果" in data["answer"]
        mock_pipeline.answer.assert_called_once_with("苹果的产地？")
