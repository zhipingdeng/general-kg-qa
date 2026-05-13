"""Tests for User model."""
import pytest
from sqlalchemy import inspect, text
from backend.app.database.mysql import Base, get_engine


def test_user_creation():
    """Test creating a User object with correct fields."""
    from backend.app.models.user import User

    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$hashed_value_here",
        is_active=True,
    )
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.hashed_password == "$2b$12$hashed_value_here"
    assert user.is_active is True


def test_user_table_exists():
    """Test that the users table is created with correct columns."""
    from backend.app.models.user import User

    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("DESCRIBE users"))
            columns = {row[0] for row in result.fetchall()}

        assert "id" in columns
        assert "username" in columns
        assert "email" in columns
        assert "hashed_password" in columns
        assert "is_active" in columns
        assert "created_at" in columns
        assert "updated_at" in columns
    finally:
        # Cleanup: drop all tables to avoid polluting other tests
        Base.metadata.drop_all(bind=engine)
