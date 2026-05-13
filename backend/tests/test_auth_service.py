"""Tests for auth service functions."""
import pytest
import time
import jwt


def test_hash_and_verify():
    """Test password hashing and verification."""
    from backend.app.services.auth import hash_password, verify_password

    password = "my_secure_password_123"
    hashed = hash_password(password)

    # Hash should be different from the original password
    assert hashed != password
    # Verify correct password
    assert verify_password(password, hashed) is True
    # Verify wrong password
    assert verify_password("wrong_password", hashed) is False


def test_create_and_decode_token():
    """Test JWT token creation and decoding."""
    from backend.app.services.auth import create_access_token, decode_access_token

    secret = "test-secret-key"
    data = {"sub": "42"}
    token = create_access_token(data, secret=secret, algorithm="HS256", hours=1)

    assert isinstance(token, str)
    assert len(token) > 0

    decoded = decode_access_token(token, secret=secret, algorithm="HS256")
    assert decoded["sub"] == "42"
    assert "exp" in decoded


def test_expired_token():
    """Test that an expired token raises ExpiredSignatureError."""
    from backend.app.services.auth import create_access_token, decode_access_token

    secret = "test-secret-key"
    # Create a token that expires immediately (negative hours)
    data = {"sub": "42"}
    token = create_access_token(data, secret=secret, algorithm="HS256", hours=-1)

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token, secret=secret, algorithm="HS256")
