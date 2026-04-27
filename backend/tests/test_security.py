import pytest
from datetime import timedelta
from fastapi import HTTPException

from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_hash_password_produces_verifiable_hash():
    pw = "s3cret-pass"
    h = hash_password(pw)
    assert h != pw
    assert verify_password(pw, h) is True


def test_verify_password_rejects_wrong_password():
    h = hash_password("right-password")
    assert verify_password("wrong-password", h) is False


def test_hash_password_produces_different_salts():
    assert hash_password("same") != hash_password("same")


def test_access_token_roundtrip_encodes_type_and_sub():
    token = create_access_token({"sub": "user-123"})
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_refresh_token_has_refresh_type():
    token = create_refresh_token({"sub": "user-xyz"})
    payload = decode_token(token)
    assert payload["type"] == "refresh"


def test_access_token_custom_expiry_is_respected():
    token = create_access_token({"sub": "u"}, expires_delta=timedelta(seconds=1))
    payload = decode_token(token)
    assert "exp" in payload


def test_decode_token_raises_401_on_tamper():
    token = create_access_token({"sub": "u"})
    tampered = token[:-4] + "XXXX"
    with pytest.raises(HTTPException) as exc:
        decode_token(tampered)
    assert exc.value.status_code == 401
