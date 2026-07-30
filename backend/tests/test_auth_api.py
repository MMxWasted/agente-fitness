from collections.abc import Callable, Generator
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from unittest.mock import Mock
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.routes import auth as auth_routes
from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.db.session import get_db_session
from app.main import app
from app.models.user import User
from app.services.auth import EmailAlreadyRegisteredError

client = TestClient(app)


def build_user(*, is_active: bool = True) -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        email="person@example.com",
        password_hash="never-exposed-stored-hash",
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )


def build_session_override(
    session: Session,
) -> Callable[[], Generator[Session]]:
    def override_session() -> Generator[Session]:
        yield session

    return override_session


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Generator[None]:
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_register_returns_public_user_without_password_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = build_user()
    session = Mock(spec=Session)
    app.dependency_overrides[get_db_session] = build_session_override(session)
    monkeypatch.setattr(
        auth_routes,
        "register_user",
        lambda _session, _registration: user,
    )

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "Person@Example.com",
            "password": token_urlsafe(32),
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": str(user.id),
        "email": user.email,
        "is_active": True,
        "created_at": user.created_at.isoformat().replace("+00:00", "Z"),
        "updated_at": user.updated_at.isoformat().replace("+00:00", "Z"),
    }
    assert "password" not in response.text


def test_register_returns_conflict_for_duplicate_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock(spec=Session)
    app.dependency_overrides[get_db_session] = build_session_override(session)

    def duplicate_registration(_session: Session, _registration: object) -> User:
        raise EmailAlreadyRegisteredError

    monkeypatch.setattr(
        auth_routes,
        "register_user",
        duplicate_registration,
    )

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "person@example.com",
            "password": token_urlsafe(32),
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("not-an-email", token_urlsafe(32)),
        ("person@example.com", "short"),
        ("person@example.com", "x" * 129),
    ],
)
def test_register_rejects_invalid_identity_input(
    email: str,
    password: str,
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )

    assert response.status_code == 422


def test_register_rejects_internal_fields_from_the_client() -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "person@example.com",
            "password": token_urlsafe(32),
            "is_active": False,
            "password_hash": "client-controlled",
        },
    )

    assert response.status_code == 422


def test_token_endpoint_returns_a_bearer_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = build_user()
    session = Mock(spec=Session)
    app.dependency_overrides[get_db_session] = build_session_override(session)
    monkeypatch.setattr(
        auth_routes,
        "authenticate_user",
        lambda _session, email, password: user,
    )

    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": user.email,
            "password": token_urlsafe(32),
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert isinstance(response.json()["access_token"], str)
    assert "password_hash" not in response.text


def test_token_endpoint_uses_one_generic_authentication_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock(spec=Session)
    app.dependency_overrides[get_db_session] = build_session_override(session)
    monkeypatch.setattr(
        auth_routes,
        "authenticate_user",
        lambda _session, email, password: None,
    )

    first_response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "missing@example.com",
            "password": token_urlsafe(32),
        },
    )
    second_response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "person@example.com",
            "password": token_urlsafe(32),
        },
    )

    assert first_response.status_code == second_response.status_code == 401
    assert (
        first_response.json()
        == second_response.json()
        == {"detail": "Incorrect email or password"}
    )
    assert first_response.headers["www-authenticate"] == "Bearer"


def test_current_user_returns_public_identity() -> None:
    user = build_user()
    app.dependency_overrides[get_current_user] = lambda: user

    response = client.get("/api/v1/users/me")

    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)
    assert response.json()["email"] == user.email
    assert "password" not in response.text


def test_current_user_requires_a_bearer_token() -> None:
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_invalid_or_unknown_token_is_rejected() -> None:
    session = Mock(spec=Session)
    session.get.return_value = None
    app.dependency_overrides[get_db_session] = build_session_override(session)

    malformed_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer not-a-token"},
    )
    unknown_response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {create_access_token(uuid4())}",
        },
    )

    assert malformed_response.status_code == unknown_response.status_code == 401
    assert (
        malformed_response.json()
        == unknown_response.json()
        == {"detail": "Could not validate credentials"}
    )


def test_expired_wrong_signature_and_incomplete_tokens_are_rejected() -> None:
    session = Mock(spec=Session)
    app.dependency_overrides[get_db_session] = build_session_override(session)
    now = datetime.now(UTC)
    settings = get_settings()
    incomplete_token = jwt.encode(
        {"sub": str(uuid4()), "iat": now},
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    invalid_tokens = [
        create_access_token(uuid4(), issued_at=now - timedelta(hours=1)),
        create_access_token(
            uuid4(),
            settings=Settings(
                jwt_secret_key=SecretStr(
                    "different-test-jwt-secret-that-is-at-least-32-bytes"
                )
            ),
        ),
        incomplete_token,
    ]

    for token in invalid_tokens:
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "Could not validate credentials"}

    session.get.assert_not_called()


def test_inactive_user_is_forbidden() -> None:
    user = build_user(is_active=False)
    session = Mock(spec=Session)
    session.get.return_value = user
    app.dependency_overrides[get_db_session] = build_session_override(session)

    response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {create_access_token(user.id)}",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Inactive account"}
