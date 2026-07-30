from datetime import UTC, datetime, timedelta
from unittest.mock import Mock
from uuid import uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_refresh_token
from app.models.auth_session import AuthSession
from app.models.user import User
from app.services import session as session_service
from app.services.session import (
    InvalidSessionError,
    create_user_session,
    revoke_user_session,
    rotate_user_session,
)

TEST_SETTINGS = Settings(
    jwt_secret_key=SecretStr("test-only-jwt-secret-with-at-least-32-bytes")
)
NOW = datetime(2026, 7, 30, 12, tzinfo=UTC)


def build_user(*, is_active: bool = True) -> User:
    return User(
        id=uuid4(),
        email="person@example.com",
        password_hash="opaque-password-hash",
        is_active=is_active,
        created_at=NOW,
        updated_at=NOW,
    )


def build_auth_session(
    *,
    refresh_token: str = "current-refresh-token",
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> AuthSession:
    return AuthSession(
        id=uuid4(),
        user_id=uuid4(),
        refresh_token_hash=hash_refresh_token(refresh_token),
        created_at=NOW,
        updated_at=NOW,
        expires_at=expires_at or NOW + timedelta(days=7),
        revoked_at=revoked_at,
    )


def test_session_creation_stores_only_hash_and_cleans_expired_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_session = Mock(spec=Session)
    user = build_user()
    added: list[AuthSession] = []
    cleanup_calls: list[datetime] = []
    monkeypatch.setattr(
        session_service,
        "generate_refresh_token",
        lambda: "generated-refresh-token",
    )
    monkeypatch.setattr(
        session_service,
        "add_auth_session",
        lambda _session, auth_session: added.append(auth_session),
    )
    monkeypatch.setattr(
        session_service,
        "delete_expired_auth_sessions",
        lambda _session, now: cleanup_calls.append(now),
    )

    credentials = create_user_session(
        database_session,
        user,
        settings=TEST_SETTINGS,
        now=NOW,
    )

    assert credentials.refresh_token == "generated-refresh-token"
    assert added[0].refresh_token_hash == hash_refresh_token(credentials.refresh_token)
    assert credentials.refresh_token not in repr(added[0])
    assert added[0].expires_at == NOW + timedelta(days=7)
    assert cleanup_calls == [NOW]
    database_session.commit.assert_called_once_with()


def test_rotation_replaces_hash_without_extending_absolute_expiration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_session = Mock(spec=Session)
    auth_session = build_auth_session()
    original_expiration = auth_session.expires_at
    monkeypatch.setattr(
        session_service,
        "delete_expired_auth_sessions",
        lambda _session, _now: None,
    )
    monkeypatch.setattr(
        session_service,
        "get_renewable_auth_session_for_update",
        lambda _session, _token_hash, _now: auth_session,
    )
    monkeypatch.setattr(
        session_service,
        "generate_refresh_token",
        lambda: "rotated-refresh-token",
    )

    credentials = rotate_user_session(
        database_session,
        "current-refresh-token",
        settings=TEST_SETTINGS,
        now=NOW + timedelta(hours=1),
    )

    assert credentials.refresh_token == "rotated-refresh-token"
    assert auth_session.refresh_token_hash == hash_refresh_token(
        "rotated-refresh-token"
    )
    assert credentials.refresh_expires_at == original_expiration
    database_session.commit.assert_called_once_with()


@pytest.mark.parametrize("case", ["missing", "expired", "revoked", "inactive"])
def test_invalid_session_states_share_one_error(
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    database_session = Mock(spec=Session)
    monkeypatch.setattr(
        session_service,
        "delete_expired_auth_sessions",
        lambda _session, _now: None,
    )
    monkeypatch.setattr(
        session_service,
        "get_renewable_auth_session_for_update",
        lambda _session, _token_hash, _now: None,
    )

    with pytest.raises(InvalidSessionError):
        rotate_user_session(
            database_session,
            f"{case}-refresh-token",
            settings=TEST_SETTINGS,
            now=NOW,
        )

    database_session.commit.assert_called_once_with()


def test_logout_revokes_an_active_session_idempotently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_session = Mock(spec=Session)
    auth_session = build_auth_session()
    monkeypatch.setattr(
        session_service,
        "delete_expired_auth_sessions",
        lambda _session, _now: None,
    )
    monkeypatch.setattr(
        session_service,
        "get_auth_session_for_update",
        lambda _session, _token_hash: auth_session,
    )

    revoke_user_session(
        database_session,
        "current-refresh-token",
        now=NOW,
    )
    first_revoked_at = auth_session.revoked_at
    revoke_user_session(
        database_session,
        "current-refresh-token",
        now=NOW + timedelta(minutes=1),
    )

    assert first_revoked_at == NOW
    assert auth_session.revoked_at == first_revoked_at
    assert database_session.commit.call_count == 2


def test_session_timestamps_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError):
        create_user_session(
            Mock(spec=Session),
            build_user(),
            settings=TEST_SETTINGS,
            now=datetime(2026, 7, 30, 12),
        )
