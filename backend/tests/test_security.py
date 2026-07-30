from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import uuid4

import jwt
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.security import (
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
    verify_refresh_token,
)


def build_settings(
    secret: str = "test-only-jwt-secret-with-at-least-32-bytes",
) -> Settings:
    return Settings(jwt_secret_key=SecretStr(secret))


def test_password_is_hashed_and_can_be_verified() -> None:
    password = SecretStr(token_urlsafe(32))
    wrong_password = SecretStr(token_urlsafe(32))

    stored_hash = hash_password(password)

    assert password.get_secret_value() not in stored_hash
    assert verify_password(password, stored_hash)
    assert not verify_password(wrong_password, stored_hash)


def test_refresh_token_is_random_hashed_and_compared_safely() -> None:
    refresh_token = generate_refresh_token()
    another_token = generate_refresh_token()
    stored_hash = hash_refresh_token(refresh_token)

    assert refresh_token != another_token
    assert len(refresh_token) >= 64
    assert len(stored_hash) == 64
    assert refresh_token not in stored_hash
    assert verify_refresh_token(refresh_token, stored_hash)
    assert not verify_refresh_token(another_token, stored_hash)


def test_access_token_round_trip_uses_the_user_id_as_subject() -> None:
    user_id = uuid4()
    settings = build_settings()

    token = create_access_token(user_id, settings=settings)

    assert decode_access_token(token, settings=settings) == user_id


def test_expired_access_token_is_rejected() -> None:
    settings = build_settings()
    token = create_access_token(
        uuid4(),
        settings=settings,
        issued_at=datetime.now(UTC) - timedelta(hours=1),
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token, settings=settings)


def test_token_signed_with_another_secret_is_rejected() -> None:
    token = create_access_token(uuid4(), settings=build_settings())

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(
            token,
            settings=build_settings(
                "another-test-only-jwt-secret-with-at-least-32-bytes"
            ),
        )


@pytest.mark.parametrize(
    "payload",
    [
        {"iat": datetime.now(UTC), "exp": datetime.now(UTC) + timedelta(minutes=5)},
        {"sub": str(uuid4()), "exp": datetime.now(UTC) + timedelta(minutes=5)},
        {"sub": str(uuid4()), "iat": datetime.now(UTC)},
        {
            "sub": "not-a-uuid",
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
    ],
)
def test_incomplete_or_invalid_identity_claims_are_rejected(
    payload: dict[str, object],
) -> None:
    settings = build_settings()
    token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token, settings=settings)
