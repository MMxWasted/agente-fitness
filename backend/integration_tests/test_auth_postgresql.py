from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import delete, inspect, text
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    hash_refresh_token,
    verify_password,
)
from app.db.session import get_engine, get_session_factory
from app.main import app
from app.models.auth_session import AuthSession
from app.models.user import User
from app.services.session import InvalidSessionError, rotate_user_session

pytestmark = pytest.mark.integration


@pytest.fixture
def client() -> Generator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def created_emails() -> Generator[list[str]]:
    emails: list[str] = []
    yield emails

    if not emails:
        return

    with get_session_factory()() as session:
        session.execute(delete(User).where(User.email.in_(set(emails))))
        session.commit()


def test_authentication_migrations_are_at_head_with_real_constraints() -> None:
    inspector = inspect(get_engine())

    assert "users" in inspector.get_table_names()
    assert "auth_sessions" in inspector.get_table_names()
    columns = {column["name"]: column for column in inspector.get_columns("users")}
    assert set(columns) == {
        "id",
        "email",
        "password_hash",
        "is_active",
        "created_at",
        "updated_at",
    }
    assert all(not column["nullable"] for column in columns.values())
    assert columns["created_at"]["type"].timezone
    assert columns["updated_at"]["type"].timezone
    assert inspector.get_pk_constraint("users")["name"] == "pk_users"
    unique_constraints = {
        constraint["name"]: set(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("users")
    }
    assert unique_constraints["uq_users_email"] == {"email"}

    session_columns = {
        column["name"]: column for column in inspector.get_columns("auth_sessions")
    }
    assert set(session_columns) == {
        "id",
        "user_id",
        "refresh_token_hash",
        "created_at",
        "updated_at",
        "expires_at",
        "revoked_at",
    }
    assert session_columns["revoked_at"]["nullable"]
    assert all(
        session_columns[name]["type"].timezone
        for name in ("created_at", "updated_at", "expires_at", "revoked_at")
    )
    assert inspector.get_pk_constraint("auth_sessions")["name"] == ("pk_auth_sessions")
    session_unique_constraints = {
        constraint["name"]: set(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("auth_sessions")
    }
    assert session_unique_constraints["uq_auth_sessions_refresh_token_hash"] == {
        "refresh_token_hash"
    }
    session_indexes = {
        index["name"]: set(index["column_names"])
        for index in inspector.get_indexes("auth_sessions")
    }
    assert session_indexes["ix_auth_sessions_user_id"] == {"user_id"}
    assert session_indexes["ix_auth_sessions_expires_at"] == {"expires_at"}
    foreign_keys = {
        foreign_key["name"]: foreign_key
        for foreign_key in inspector.get_foreign_keys("auth_sessions")
    }
    user_foreign_key = foreign_keys["fk_auth_sessions_user_id_users"]
    assert user_foreign_key["referred_table"] == "users"
    assert user_foreign_key["constrained_columns"] == ["user_id"]
    assert user_foreign_key["options"]["ondelete"] == "CASCADE"

    with get_engine().connect() as connection:
        revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
    assert revision == "20260731_0005"


def test_registration_login_and_current_user_flow(
    client: TestClient,
    created_emails: list[str],
) -> None:
    email = f"integration-{uuid4()}@example.com"
    submitted_email = email.upper()
    password = token_urlsafe(32)
    created_emails.append(email)

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": submitted_email, "password": password},
    )

    assert register_response.status_code == 201
    registered_user = register_response.json()
    assert registered_user["email"] == email
    assert registered_user["is_active"] is True
    assert "password" not in register_response.text

    user_id = UUID(registered_user["id"])
    with get_session_factory()() as session:
        stored_user = session.get(User, user_id)
        assert stored_user is not None
        assert stored_user.password_hash != password
        assert verify_password(SecretStr(password), stored_user.password_hash)

    duplicate_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": token_urlsafe(32)},
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {"detail": "Email already registered"}

    missing_user_response = client.post(
        "/api/v1/auth/token",
        data={
            "username": f"missing-{uuid4()}@example.com",
            "password": token_urlsafe(32),
        },
    )
    wrong_password_response = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": token_urlsafe(32)},
    )
    assert (
        missing_user_response.status_code == wrong_password_response.status_code == 401
    )
    assert (
        missing_user_response.json()
        == wrong_password_response.json()
        == {"detail": "Incorrect email or password"}
    )

    token_response = client.post(
        "/api/v1/auth/token",
        data={"username": submitted_email, "password": password},
    )
    assert token_response.status_code == 200
    assert token_response.json()["token_type"] == "bearer"
    assert token_response.json()["expires_in"] == 1800
    assert "refresh_token" not in token_response.text
    access_token = token_response.json()["access_token"]
    settings = get_settings()
    original_refresh_token = client.cookies.get(settings.refresh_cookie_name)
    assert original_refresh_token

    with get_session_factory()() as session:
        stored_auth_session = (
            session.query(AuthSession).filter_by(user_id=user_id).one()
        )
        assert stored_auth_session.refresh_token_hash == hash_refresh_token(
            original_refresh_token
        )
        assert original_refresh_token not in repr(stored_auth_session)

    current_user_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert current_user_response.status_code == 200
    assert current_user_response.json() == registered_user
    assert "password" not in current_user_response.text

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "http://localhost:5173"},
    )
    assert refresh_response.status_code == 200
    refreshed_access_token = refresh_response.json()["access_token"]
    refreshed_user_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {refreshed_access_token}"},
    )
    assert refreshed_user_response.status_code == 200
    assert refreshed_user_response.json() == registered_user
    rotated_refresh_token = client.cookies.get(settings.refresh_cookie_name)
    assert rotated_refresh_token
    assert rotated_refresh_token != original_refresh_token

    with TestClient(app) as replay_client:
        replay_client.cookies.set(
            settings.refresh_cookie_name,
            original_refresh_token,
            domain="testserver.local",
            path=settings.refresh_cookie_path,
        )
        replay_response = replay_client.post(
            "/api/v1/auth/refresh",
            headers={"Origin": "http://localhost:5173"},
        )
    assert replay_response.status_code == 401
    assert replay_response.json() == {"detail": "Could not refresh session"}

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Origin": "http://localhost:5173"},
    )
    repeated_logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Origin": "http://localhost:5173"},
    )
    assert logout_response.status_code == repeated_logout_response.status_code == 204
    with get_session_factory()() as session:
        revoked_auth_session = (
            session.query(AuthSession).filter_by(user_id=user_id).one()
        )
        assert revoked_auth_session.revoked_at is not None

    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}


def test_database_enforces_unique_normalized_email(
    created_emails: list[str],
) -> None:
    email = f"integration-unique-{uuid4()}@example.com"
    created_emails.append(email)
    first_user = User(
        id=uuid4(),
        email=email,
        password_hash="test-only-opaque-hash",
        is_active=True,
    )
    duplicate_user = User(
        id=uuid4(),
        email=email,
        password_hash="different-test-only-opaque-hash",
        is_active=True,
    )

    with get_session_factory()() as session:
        session.add(first_user)
        session.commit()
        session.add(duplicate_user)

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()


def test_database_enforces_unique_refresh_hash_and_user_foreign_key(
    created_emails: list[str],
) -> None:
    email = f"integration-session-constraints-{uuid4()}@example.com"
    created_emails.append(email)
    user = User(
        id=uuid4(),
        email=email,
        password_hash="test-only-opaque-hash",
        is_active=True,
    )
    refresh_hash = hash_refresh_token(token_urlsafe(48))
    now = datetime.now(UTC)

    with get_session_factory()() as session:
        session.add(user)
        session.commit()
        first_auth_session = AuthSession(
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            expires_at=now + timedelta(days=7),
        )
        session.add(first_auth_session)
        session.commit()

        session.add(
            AuthSession(
                user_id=user.id,
                refresh_token_hash=refresh_hash,
                expires_at=now + timedelta(days=7),
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        session.add(
            AuthSession(
                user_id=uuid4(),
                refresh_token_hash=hash_refresh_token(token_urlsafe(48)),
                expires_at=now + timedelta(days=7),
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_tokens_follow_account_state_and_identity_existence(
    client: TestClient,
    created_emails: list[str],
) -> None:
    email = f"integration-inactive-{uuid4()}@example.com"
    password = token_urlsafe(32)
    created_emails.append(email)
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    user_id = UUID(register_response.json()["id"])
    token_response = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    access_token = token_response.json()["access_token"]

    with get_session_factory()() as session:
        user = session.get(User, user_id)
        assert user is not None
        user.is_active = False
        session.commit()

    inactive_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    inactive_login_response = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    unknown_identity_response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {create_access_token(uuid4())}",
        },
    )
    malformed_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer not-a-token"},
    )
    missing_response = client.get("/api/v1/users/me")
    inactive_refresh_response = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "http://localhost:5173"},
    )

    assert inactive_response.status_code == 403
    assert inactive_login_response.status_code == 401
    assert inactive_refresh_response.status_code == 401
    assert unknown_identity_response.status_code == 401
    assert malformed_response.status_code == 401
    assert missing_response.status_code == 401


def test_expired_and_revoked_sessions_share_the_generic_refresh_error(
    client: TestClient,
    created_emails: list[str],
) -> None:
    settings = get_settings()
    email = f"integration-expired-{uuid4()}@example.com"
    password = token_urlsafe(32)
    created_emails.append(email)
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    user_id = UUID(register_response.json()["id"])
    client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )

    with get_session_factory()() as session:
        auth_session = session.query(AuthSession).filter_by(user_id=user_id).one()
        auth_session.created_at = datetime.now(UTC) - timedelta(days=8)
        auth_session.expires_at = datetime.now(UTC) - timedelta(days=1)
        session.commit()

    expired_response = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "http://localhost:5173"},
    )

    new_login_response = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    assert new_login_response.status_code == 200
    revoked_refresh_token = client.cookies.get(settings.refresh_cookie_name)
    assert revoked_refresh_token
    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Origin": "http://localhost:5173"},
    )
    assert logout_response.status_code == 204

    with TestClient(app) as replay_client:
        replay_client.cookies.set(
            settings.refresh_cookie_name,
            revoked_refresh_token,
            domain="testserver.local",
            path=settings.refresh_cookie_path,
        )
        revoked_response = replay_client.post(
            "/api/v1/auth/refresh",
            headers={"Origin": "http://localhost:5173"},
        )

    assert expired_response.status_code == revoked_response.status_code == 401
    assert (
        expired_response.json()
        == revoked_response.json()
        == {"detail": "Could not refresh session"}
    )


def test_concurrent_refresh_allows_at_most_one_rotation(
    client: TestClient,
    created_emails: list[str],
) -> None:
    email = f"integration-concurrent-{uuid4()}@example.com"
    password = token_urlsafe(32)
    created_emails.append(email)
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200
    refresh_token = client.cookies.get(get_settings().refresh_cookie_name)
    assert refresh_token
    barrier = Barrier(2)

    def rotate_once() -> bool:
        barrier.wait()
        with get_session_factory()() as session:
            try:
                rotate_user_session(session, refresh_token)
            except InvalidSessionError:
                return False
            return True

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: rotate_once(), range(2)))

    assert sorted(results) == [False, True]
