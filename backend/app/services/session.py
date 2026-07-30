from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.models.auth_session import AuthSession
from app.models.user import User
from app.repositories.auth_session import (
    add_auth_session,
    delete_expired_auth_sessions,
    get_auth_session_for_update,
    get_renewable_auth_session_for_update,
)


class InvalidSessionError(ValueError):
    """Raised when a refresh credential cannot renew a session."""


@dataclass(frozen=True)
class SessionCredentials:
    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)
    refresh_expires_at: datetime


def create_user_session(
    session: Session,
    user: User,
    *,
    settings: Settings | None = None,
    now: datetime | None = None,
) -> SessionCredentials:
    session_settings = settings or get_settings()
    current_time = _as_utc(now or datetime.now(UTC))
    refresh_token = generate_refresh_token()
    expires_at = current_time + timedelta(
        days=session_settings.refresh_token_expire_days
    )
    auth_session = AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(refresh_token),
        created_at=current_time,
        updated_at=current_time,
        expires_at=expires_at,
    )

    delete_expired_auth_sessions(session, current_time)
    add_auth_session(session, auth_session)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise

    return SessionCredentials(
        access_token=create_access_token(
            user.id,
            settings=session_settings,
            issued_at=current_time,
        ),
        refresh_token=refresh_token,
        refresh_expires_at=expires_at,
    )


def rotate_user_session(
    session: Session,
    refresh_token: str,
    *,
    settings: Settings | None = None,
    now: datetime | None = None,
) -> SessionCredentials:
    session_settings = settings or get_settings()
    current_time = _as_utc(now or datetime.now(UTC))
    current_hash = hash_refresh_token(refresh_token)

    delete_expired_auth_sessions(session, current_time)
    auth_session = get_renewable_auth_session_for_update(
        session,
        current_hash,
        current_time,
    )
    if auth_session is None:
        session.commit()
        raise InvalidSessionError

    rotated_token = generate_refresh_token()
    auth_session.refresh_token_hash = hash_refresh_token(rotated_token)
    auth_session.updated_at = current_time
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise

    return SessionCredentials(
        access_token=create_access_token(
            auth_session.user_id,
            settings=session_settings,
            issued_at=current_time,
        ),
        refresh_token=rotated_token,
        refresh_expires_at=auth_session.expires_at,
    )


def revoke_user_session(
    session: Session,
    refresh_token: str | None,
    *,
    now: datetime | None = None,
) -> None:
    current_time = _as_utc(now or datetime.now(UTC))
    delete_expired_auth_sessions(session, current_time)

    if refresh_token:
        auth_session = get_auth_session_for_update(
            session,
            hash_refresh_token(refresh_token),
        )
        if auth_session is not None and auth_session.revoked_at is None:
            auth_session.revoked_at = current_time
            auth_session.updated_at = current_time

    try:
        session.commit()
    except Exception:
        session.rollback()
        raise


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Session timestamps must be timezone-aware")
    return value.astimezone(UTC)
