import pytest
from sqlalchemy import text
from backend.app.database.mysql import Base, get_engine, get_session_local


def test_engine_creation():
    engine = get_engine()
    assert engine is not None


def test_create_tables():
    engine = get_engine()
    # Import the actual User model so it's registered with Base.metadata
    from backend.app.models.user import User  # noqa: F401

    Base.metadata.create_all(bind=engine)

    try:
        # Verify the users table exists via SHOW TABLES
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            assert "users" in tables
    finally:
        # Cleanup: drop the test table
        Base.metadata.drop_all(bind=engine)
