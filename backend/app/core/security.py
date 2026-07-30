from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from pydantic import SecretStr

from app.core.config import Settings, get_settings

_password_hash = PasswordHash.recommended()
_dummy_password_hash = _password_hash.hash(token_urlsafe(32))


class InvalidAccessTokenError(ValueError):
    """Raised when an access token cannot establish a valid identity."""


def hash_password(password: SecretStr) -> str:
    return _password_hash.hash(password.get_secret_value())


def verify_password(password: SecretStr, stored_hash: str) -> bool:
    try:
        return _password_hash.verify(password.get_secret_value(), stored_hash)
    except (UnknownHashError, ValueError):
        return False


def verify_password_and_update(
    password: SecretStr,
    stored_hash: str,
) -> tuple[bool, str | None]:
    try:
        return _password_hash.verify_and_update(
            password.get_secret_value(),
            stored_hash,
        )
    except (UnknownHashError, ValueError):
        return False, None


def perform_dummy_password_verification(password: SecretStr) -> None:
    verify_password(password, _dummy_password_hash)


def create_access_token(
    user_id: UUID,
    *,
    settings: Settings | None = None,
    issued_at: datetime | None = None,
) -> str:
    token_settings = settings or get_settings()
    now = issued_at or datetime.now(UTC)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("issued_at must be timezone-aware")

    now = now.astimezone(UTC)
    expires_at = now + timedelta(minutes=token_settings.access_token_expire_minutes)
    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": now,
            "exp": expires_at,
        },
        token_settings.jwt_secret_key.get_secret_value(),
        algorithm=token_settings.jwt_algorithm,
    )


def decode_access_token(
    token: str,
    *,
    settings: Settings | None = None,
) -> UUID:
    token_settings = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            token_settings.jwt_secret_key.get_secret_value(),
            algorithms=[token_settings.jwt_algorithm],
            options={
                "require": ["sub", "iat", "exp"],
                "verify_exp": True,
                "verify_iat": True,
                "verify_sub": True,
            },
        )
        subject = payload["sub"]
        if not isinstance(subject, str):
            raise InvalidAccessTokenError
        return UUID(subject)
    except (InvalidTokenError, KeyError, TypeError, ValueError) as error:
        raise InvalidAccessTokenError from error
