from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from secrets import token_urlsafe
from threading import Barrier, local
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.db.session import get_engine, get_session_factory
from app.main import app
from app.models.user import User
from app.models.user_profile import UserProfile
from app.repositories.user_profile import get_user_profile_by_user_id
from app.schemas.profile import ProfileUpsert
from app.services import profile as profile_service
from app.services.profile import put_user_profile

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


def register_and_login(
    client: TestClient,
    created_emails: list[str],
    *,
    prefix: str,
) -> tuple[UUID, str]:
    email = f"{prefix}-{uuid4()}@example.com"
    password = token_urlsafe(32)
    created_emails.append(email)
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200
    return (
        UUID(register_response.json()["id"]),
        login_response.json()["access_token"],
    )


def profile_payload(
    *,
    display_name: str = "Alex",
    unit_system: str = "metric",
) -> dict[str, object]:
    return {
        "display_name": display_name,
        "birth_date": "1995-05-12",
        "height_cm": 178.25,
        "experience_level": "intermediate",
        "timezone": "Europe/Madrid",
        "unit_system": unit_system,
    }


def authorization(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_profile_migration_is_at_head_with_real_constraints() -> None:
    inspector = inspect(get_engine())

    assert "user_profiles" in inspector.get_table_names()
    columns = {
        column["name"]: column for column in inspector.get_columns("user_profiles")
    }
    assert set(columns) == {
        "id",
        "user_id",
        "display_name",
        "birth_date",
        "height_cm",
        "experience_level",
        "timezone",
        "unit_system",
        "created_at",
        "updated_at",
    }
    assert columns["birth_date"]["nullable"]
    assert columns["height_cm"]["nullable"]
    assert all(
        not columns[name]["nullable"]
        for name in (
            "id",
            "user_id",
            "display_name",
            "experience_level",
            "timezone",
            "unit_system",
            "created_at",
            "updated_at",
        )
    )
    assert columns["height_cm"]["type"].precision == 5
    assert columns["height_cm"]["type"].scale == 2
    assert columns["created_at"]["type"].timezone
    assert columns["updated_at"]["type"].timezone
    assert inspector.get_pk_constraint("user_profiles")["name"] == ("pk_user_profiles")

    unique_constraints = {
        constraint["name"]: set(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("user_profiles")
    }
    assert unique_constraints["uq_user_profiles_user_id"] == {"user_id"}

    check_constraints = {
        constraint["name"]
        for constraint in inspector.get_check_constraints("user_profiles")
    }
    assert {
        "ck_user_profiles_display_name_not_blank",
        "ck_user_profiles_height_cm_range",
        "ck_user_profiles_experience_level",
        "ck_user_profiles_unit_system",
    } <= check_constraints

    foreign_keys = {
        foreign_key["name"]: foreign_key
        for foreign_key in inspector.get_foreign_keys("user_profiles")
    }
    user_foreign_key = foreign_keys["fk_user_profiles_user_id_users"]
    assert user_foreign_key["referred_table"] == "users"
    assert user_foreign_key["constrained_columns"] == ["user_id"]
    assert user_foreign_key["options"]["ondelete"] == "CASCADE"

    with get_engine().connect() as connection:
        revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
    assert revision == "20260730_0004"


def test_profile_api_is_idempotent_and_isolated_between_users(
    client: TestClient,
    created_emails: list[str],
) -> None:
    first_user_id, first_access_token = register_and_login(
        client,
        created_emails,
        prefix="profile-first",
    )
    second_user_id, second_access_token = register_and_login(
        client,
        created_emails,
        prefix="profile-second",
    )

    missing_response = client.get(
        "/api/v1/profile",
        headers=authorization(first_access_token),
    )
    assert missing_response.status_code == 404

    create_response = client.put(
        "/api/v1/profile",
        headers=authorization(first_access_token),
        json=profile_payload(),
    )
    repeated_response = client.put(
        "/api/v1/profile",
        headers=authorization(first_access_token),
        json=profile_payload(),
    )
    assert create_response.status_code == repeated_response.status_code == 200
    assert create_response.json() == repeated_response.json()
    assert "user_id" not in create_response.json()

    second_missing_response = client.get(
        "/api/v1/profile",
        headers=authorization(second_access_token),
    )
    assert second_missing_response.status_code == 404

    second_create_response = client.put(
        "/api/v1/profile",
        headers=authorization(second_access_token),
        json=profile_payload(
            display_name="Second user",
            unit_system="imperial",
        ),
    )
    assert second_create_response.status_code == 200

    first_profile_response = client.get(
        "/api/v1/profile",
        headers=authorization(first_access_token),
        params={"user_id": str(second_user_id)},
    )
    assert first_profile_response.status_code == 200
    assert first_profile_response.json()["display_name"] == "Alex"
    assert first_profile_response.json()["id"] != second_create_response.json()["id"]

    forbidden_owner_payload = profile_payload()
    forbidden_owner_payload["user_id"] = str(second_user_id)
    owner_override_response = client.put(
        "/api/v1/profile",
        headers=authorization(first_access_token),
        json=forbidden_owner_payload,
    )
    assert owner_override_response.status_code == 422

    clear_optional_payload = profile_payload(display_name="Updated")
    clear_optional_payload.pop("birth_date")
    clear_optional_payload.pop("height_cm")
    update_response = client.put(
        "/api/v1/profile",
        headers=authorization(first_access_token),
        json=clear_optional_payload,
    )
    assert update_response.status_code == 200
    assert update_response.json()["birth_date"] is None
    assert update_response.json()["height_cm"] is None

    with get_session_factory()() as session:
        first_profile = get_user_profile_by_user_id(session, first_user_id)
        second_profile = get_user_profile_by_user_id(session, second_user_id)
        assert first_profile is not None
        assert second_profile is not None
        assert first_profile.display_name == "Updated"
        assert second_profile.display_name == "Second user"

    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}
    current_user_response = client.get(
        "/api/v1/users/me",
        headers=authorization(first_access_token),
    )
    assert current_user_response.status_code == 200
    assert current_user_response.json()["id"] == str(first_user_id)


def test_database_enforces_profile_constraints_and_cascade(
    created_emails: list[str],
) -> None:
    email = f"profile-constraints-{uuid4()}@example.com"
    invalid_email = f"profile-invalid-{uuid4()}@example.com"
    created_emails.extend([email, invalid_email])
    user = User(
        id=uuid4(),
        email=email,
        password_hash="test-only-opaque-hash",
        is_active=True,
    )
    invalid_user = User(
        id=uuid4(),
        email=invalid_email,
        password_hash="test-only-opaque-hash",
        is_active=True,
    )

    with get_session_factory()() as session:
        session.add_all([user, invalid_user])
        session.commit()
        profile = UserProfile(
            user_id=user.id,
            display_name="Constraint owner",
            experience_level="beginner",
            timezone="UTC",
            unit_system="metric",
        )
        session.add(profile)
        session.commit()
        profile_id = profile.id

        session.add(
            UserProfile(
                user_id=user.id,
                display_name="Duplicate",
                experience_level="advanced",
                timezone="UTC",
                unit_system="metric",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        session.add(
            UserProfile(
                user_id=invalid_user.id,
                display_name="Invalid height",
                height_cm=Decimal("301"),
                experience_level="beginner",
                timezone="UTC",
                unit_system="metric",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        session.delete(user)
        session.commit()
        assert session.get(UserProfile, profile_id) is None


def test_concurrent_profile_creation_returns_one_profile(
    monkeypatch: pytest.MonkeyPatch,
    created_emails: list[str],
) -> None:
    email = f"profile-concurrent-{uuid4()}@example.com"
    created_emails.append(email)
    user_id = uuid4()
    with get_session_factory()() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                password_hash="test-only-opaque-hash",
                is_active=True,
            )
        )
        session.commit()

    barrier = Barrier(2)
    thread_state = local()
    original_lookup = get_user_profile_by_user_id

    def synchronized_initial_lookup(
        session: object,
        lookup_user_id: UUID,
    ) -> UserProfile | None:
        result = original_lookup(session, lookup_user_id)  # type: ignore[arg-type]
        if not getattr(thread_state, "initial_lookup_done", False):
            thread_state.initial_lookup_done = True
            assert result is None
            barrier.wait()
        return result

    monkeypatch.setattr(
        profile_service,
        "get_user_profile_by_user_id",
        synchronized_initial_lookup,
    )
    profile_data = ProfileUpsert(
        display_name="Concurrent",
        birth_date=date(1995, 5, 12),
        height_cm=Decimal("178.25"),
        experience_level="intermediate",
        timezone="Europe/Madrid",
        unit_system="metric",
    )

    def create_profile() -> UUID:
        with get_session_factory()() as session:
            user = session.get(User, user_id)
            assert user is not None
            return put_user_profile(session, user, profile_data).id

    with ThreadPoolExecutor(max_workers=2) as executor:
        profile_ids = list(executor.map(lambda _index: create_profile(), range(2)))

    assert profile_ids[0] == profile_ids[1]
    with get_session_factory()() as session:
        profile_count = session.scalar(
            select(func.count())
            .select_from(UserProfile)
            .where(UserProfile.user_id == user_id)
        )
    assert profile_count == 1
