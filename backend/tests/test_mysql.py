import pytest
from sqlalchemy import text
from backend.app.database.mysql import Base, get_engine, get_session_local


def test_engine_creation():
    engine = get_engine()
    assert engine is not None


def test_create_tables():
    engine = get_engine()
    # Import all models so they are registered with Base.metadata
    # Define a simple User model inline for testing
    from sqlalchemy import Column, Integer, String

    class User(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True, autoincrement=True)
        username = Column(String(50), unique=True, nullable=False)

    Base.metadata.create_all(bind=engine)

    # Verify the users table exists via SHOW TABLES
    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result.fetchall()]
        assert "users" in tables

    # Cleanup: drop the test table
    Base.metadata.drop_all(bind=engine)
