from collections.abc import Callable, Generator
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.routes import profile as profile_routes
from app.core.security import create_access_token
from app.db.session import get_db_session
from app.main import app
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.profile import ProfileUpsert

client = TestClient(app)
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


def build_profile(user: User) -> UserProfile:
    return UserProfile(
        id=uuid4(),
        user_id=user.id,
        display_name="Alex",
        birth_date=date(1995, 5, 12),
        height_cm=Decimal("178.25"),
        experience_level="intermediate",
        timezone="Europe/Madrid",
        unit_system="metric",
        created_at=NOW,
        updated_at=NOW,
    )


def profile_payload() -> dict[str, object]:
    return {
        "display_name": "Alex",
        "birth_date": "1995-05-12",
        "height_cm": 178.25,
        "experience_level": "intermediate",
        "timezone": "Europe/Madrid",
        "unit_system": "metric",
    }


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


def test_profile_requires_a_bearer_token() -> None:
    get_response = client.get("/api/v1/profile")
    put_response = client.put("/api/v1/profile", json=profile_payload())

    assert get_response.status_code == put_response.status_code == 401
    assert get_response.headers["www-authenticate"] == "Bearer"


def test_profile_rejects_invalid_and_inactive_identities() -> None:
    session = Mock(spec=Session)
    inactive_user = build_user(is_active=False)
    session.get.return_value = inactive_user
    app.dependency_overrides[get_db_session] = build_session_override(session)

    invalid_response = client.get(
        "/api/v1/profile",
        headers={"Authorization": "Bearer not-a-token"},
    )
    inactive_response = client.get(
        "/api/v1/profile",
        headers={
            "Authorization": f"Bearer {create_access_token(inactive_user.id)}",
        },
    )

    assert invalid_response.status_code == 401
    assert inactive_response.status_code == 403


def test_get_returns_404_until_the_authenticated_user_has_a_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = build_user()
    session = Mock(spec=Session)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db_session] = build_session_override(session)
    monkeypatch.setattr(
        profile_routes,
        "get_user_profile",
        lambda _session, _user: None,
    )

    response = client.get("/api/v1/profile")

    assert response.status_code == 404
    assert response.json() == {"detail": "Profile not found"}


def test_get_returns_only_the_authenticated_users_public_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = build_user()
    profile = build_profile(user)
    session = Mock(spec=Session)
    received_users: list[User] = []
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db_session] = build_session_override(session)

    def find_profile(
        _session: Session,
        current_user: User,
    ) -> UserProfile:
        received_users.append(current_user)
        return profile

    monkeypatch.setattr(
        profile_routes,
        "get_user_profile",
        find_profile,
    )

    response = client.get(
        "/api/v1/profile",
        params={"user_id": str(uuid4())},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(profile.id)
    assert response.json()["height_cm"] == 178.25
    assert "user_id" not in response.json()
    assert received_users == [user]


def test_put_creates_or_replaces_the_current_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = build_user()
    profile = build_profile(user)
    session = Mock(spec=Session)
    received_users: list[User] = []
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db_session] = build_session_override(session)

    def replace_profile(
        _session: Session,
        current_user: User,
        profile_data: ProfileUpsert,
    ) -> UserProfile:
        received_users.append(current_user)
        assert profile_data.display_name == "Alex"
        return profile

    monkeypatch.setattr(
        profile_routes,
        "put_user_profile",
        replace_profile,
    )

    response = client.put("/api/v1/profile", json=profile_payload())

    assert response.status_code == 200
    assert response.json()["display_name"] == "Alex"
    assert received_users == [user]


@pytest.mark.parametrize(
    "internal_field",
    ["id", "user_id", "created_at", "updated_at", "unknown"],
)
def test_put_rejects_internal_and_extra_fields(internal_field: str) -> None:
    user = build_user()
    app.dependency_overrides[get_current_user] = lambda: user
    payload = profile_payload()
    payload[internal_field] = str(uuid4())

    response = client.put("/api/v1/profile", json=payload)

    assert response.status_code == 422


def test_put_is_full_replacement_with_required_context() -> None:
    user = build_user()
    app.dependency_overrides[get_current_user] = lambda: user
    payload = profile_payload()
    payload.pop("timezone")

    response = client.put("/api/v1/profile", json=payload)

    assert response.status_code == 422


def test_openapi_documents_profile_security_and_closed_input() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    get_contract = paths["/api/v1/profile"]["get"]
    put_contract = paths["/api/v1/profile"]["put"]
    assert {"200", "401", "403", "404"} <= set(get_contract["responses"])
    assert {"200", "401", "403", "422"} <= set(put_contract["responses"])
    assert get_contract["security"] == [{"OAuth2PasswordBearer": []}]
    assert put_contract["security"] == [{"OAuth2PasswordBearer": []}]

    schemas = response.json()["components"]["schemas"]
    input_properties = schemas["ProfileUpsert"]["properties"]
    assert "user_id" not in input_properties
    assert "id" not in input_properties
    assert "created_at" not in input_properties
    assert "updated_at" not in input_properties
