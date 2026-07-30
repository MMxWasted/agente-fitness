from collections.abc import Generator
from secrets import token_urlsafe
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import delete, inspect, text
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, verify_password
from app.db.session import get_engine, get_session_factory
from app.main import app
from app.models.user import User

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


def test_users_migration_is_at_head_with_real_constraints() -> None:
    inspector = inspect(get_engine())

    assert "users" in inspector.get_table_names()
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

    with get_engine().connect() as connection:
        revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
    assert revision == "20260730_0002"


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
    access_token = token_response.json()["access_token"]

    current_user_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert current_user_response.status_code == 200
    assert current_user_response.json() == registered_user
    assert "password" not in current_user_response.text

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

    assert inactive_response.status_code == 403
    assert inactive_login_response.status_code == 401
    assert unknown_identity_response.status_code == 401
    assert malformed_response.status_code == 401
    assert missing_response.status_code == 401
