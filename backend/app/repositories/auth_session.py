from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.auth_session import AuthSession
from app.models.user import User


def add_auth_session(
    session: Session,
    auth_session: AuthSession,
) -> None:
    session.add(auth_session)


def get_renewable_auth_session_for_update(
    session: Session,
    refresh_token_hash: str,
    now: datetime,
) -> AuthSession | None:
    statement = (
        select(AuthSession)
        .join(User, User.id == AuthSession.user_id)
        .where(
            AuthSession.refresh_token_hash == refresh_token_hash,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
            User.is_active.is_(True),
        )
        .with_for_update(of=AuthSession)
    )
    return session.scalar(statement)


def get_auth_session_for_update(
    session: Session,
    refresh_token_hash: str,
) -> AuthSession | None:
    statement = (
        select(AuthSession)
        .where(AuthSession.refresh_token_hash == refresh_token_hash)
        .with_for_update()
    )
    return session.scalar(statement)


def delete_expired_auth_sessions(
    session: Session,
    now: datetime,
) -> None:
    session.execute(delete(AuthSession).where(AuthSession.expires_at <= now))
