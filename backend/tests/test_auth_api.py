"""Tests for auth API endpoints."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from backend.app.database.mysql import Base, get_engine
from backend.app.models.user import User  # ensure User model is registered with Base.metadata


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test and drop after."""
    engine = get_engine()
    # Ensure all models are imported so metadata is complete
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest_asyncio.fixture
async def client():
    """Create a test HTTP client with the auth router."""
    from backend.app.api.v1.auth import router as auth_router

    test_app = FastAPI()
    test_app.include_router(auth_router, prefix="/api/v1")
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_register_success(client):
    """Test successful user registration."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "email": "new@example.com", "password": "pass123456"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["username"] == "newuser"
    assert data["user"]["email"] == "new@example.com"
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate(client):
    """Test registration with duplicate username."""
    await client.post(
        "/api/v1/auth/register",
        json={"username": "dupuser", "email": "dup@example.com", "password": "pass123456"},
    )
    resp = await client.post(
        "/api/v1/auth/register",
        json={"username": "dupuser", "email": "dup@example.com", "password": "pass123456"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client):
    """Test successful login."""
    await client.post(
        "/api/v1/auth/register",
        json={"username": "loginuser", "email": "login@example.com", "password": "pass123456"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "loginuser", "password": "pass123456"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """Test login with wrong password."""
    await client.post(
        "/api/v1/auth/register",
        json={"username": "wrongpw", "email": "wrong@example.com", "password": "pass123456"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "wrongpw", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_requires_auth(client):
    """Test that /me endpoint requires authentication."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_token(client):
    """Test /me endpoint with valid token."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"username": "meuser", "email": "me@example.com", "password": "pass123456"},
    )
    token = reg.json()["access_token"]
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "meuser"
