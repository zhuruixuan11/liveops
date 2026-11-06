from datetime import timedelta

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("123456")
    assert hashed != "123456"
    assert verify_password("123456", hashed)
    assert not verify_password("wrong-password", hashed)


def test_token_contains_sub_and_role():
    token = create_access_token(sub="42", role="ADMIN")
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["role"] == "ADMIN"


def test_expired_token_is_rejected():
    token = create_access_token(sub="1", expires_delta=timedelta(seconds=-1))
    assert decode_token(token) is None


def test_tampered_token_is_rejected():
    token = create_access_token(sub="1")
    assert decode_token(token + "x") is None
