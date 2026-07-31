from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.profile import ProfileUpsert
from app.services import profile as profile_service
from app.services.profile import get_user_profile, put_user_profile

NOW = datetime(2026, 7, 30, 12, tzinfo=UTC)


def build_user() -> User:
    return User(
        id=uuid4(),
        email="person@example.com",
        password_hash="opaque-password-hash",
        is_active=True,
        created_at=NOW,
        updated_at=NOW,
    )


def build_profile_data(
    *,
    display_name: str = "Alex",
    birth_date_value: date | None = date(1995, 5, 12),
    height_cm: Decimal | None = Decimal("178.25"),
) -> ProfileUpsert:
    return ProfileUpsert(
        display_name=display_name,
        birth_date=birth_date_value,
        height_cm=height_cm,
        experience_level="intermediate",
        timezone="Europe/Madrid",
        unit_system="metric",
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


def test_get_profile_uses_only_the_authenticated_user_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock(spec=Session)
    user = build_user()
    expected = build_profile(user)
    received_user_ids: list[object] = []

    def find_profile(
        _session: Session,
        user_id: object,
    ) -> UserProfile:
        received_user_ids.append(user_id)
        return expected

    monkeypatch.setattr(
        profile_service,
        "get_user_profile_by_user_id",
        find_profile,
    )

    result = get_user_profile(session, user)

    assert result is expected
    assert received_user_ids == [user.id]


def test_put_creates_a_profile_for_the_authenticated_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock(spec=Session)
    user = build_user()
    added: list[UserProfile] = []
    monkeypatch.setattr(
        profile_service,
        "get_user_profile_by_user_id",
        lambda _session, _user_id: None,
    )
    monkeypatch.setattr(
        profile_service,
        "add_user_profile",
        lambda _session, profile: added.append(profile),
    )

    result = put_user_profile(session, user, build_profile_data())

    assert result is added[0]
    assert result.user_id == user.id
    assert result.display_name == "Alex"
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(result)


def test_repeating_the_same_put_does_not_write_again(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock(spec=Session)
    user = build_user()
    existing = build_profile(user)
    monkeypatch.setattr(
        profile_service,
        "get_user_profile_by_user_id",
        lambda _session, _user_id: existing,
    )

    result = put_user_profile(session, user, build_profile_data())

    assert result is existing
    session.commit.assert_not_called()
    session.refresh.assert_called_once_with(existing)


def test_put_replaces_all_fields_and_clears_optional_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock(spec=Session)
    user = build_user()
    existing = build_profile(user)
    monkeypatch.setattr(
        profile_service,
        "get_user_profile_by_user_id",
        lambda _session, _user_id: existing,
    )

    result = put_user_profile(
        session,
        user,
        build_profile_data(
            display_name="Updated",
            birth_date_value=None,
            height_cm=None,
        ),
    )

    assert result.display_name == "Updated"
    assert result.birth_date is None
    assert result.height_cm is None
    session.commit.assert_called_once_with()


def test_unique_creation_race_reloads_and_updates_the_winning_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock(spec=Session)
    user = build_user()
    winner = build_profile(user)
    winner.display_name = "Other request"
    lookups = iter([None, winner])

    class Diagnostics:
        constraint_name = "uq_user_profiles_user_id"

    class OriginalDatabaseError(Exception):
        diag = Diagnostics()

    session.commit.side_effect = [
        IntegrityError(
            "INSERT INTO user_profiles",
            {},
            OriginalDatabaseError(),
        ),
        None,
    ]
    monkeypatch.setattr(
        profile_service,
        "get_user_profile_by_user_id",
        lambda _session, _user_id: next(lookups),
    )
    monkeypatch.setattr(
        profile_service,
        "add_user_profile",
        lambda _session, _profile: None,
    )

    result = put_user_profile(session, user, build_profile_data())

    assert result is winner
    assert result.display_name == "Alex"
    assert session.commit.call_count == 2
    session.rollback.assert_called_once_with()


def test_unrelated_integrity_error_is_not_hidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock(spec=Session)
    user = build_user()

    class Diagnostics:
        constraint_name = "ck_unrelated"

    class OriginalDatabaseError(Exception):
        diag = Diagnostics()

    database_error = IntegrityError(
        "INSERT INTO user_profiles",
        {},
        OriginalDatabaseError(),
    )
    session.commit.side_effect = database_error
    monkeypatch.setattr(
        profile_service,
        "get_user_profile_by_user_id",
        lambda _session, _user_id: None,
    )
    monkeypatch.setattr(
        profile_service,
        "add_user_profile",
        lambda _session, _profile: None,
    )

    with pytest.raises(IntegrityError) as captured:
        put_user_profile(session, user, build_profile_data())

    assert captured.value is database_error
    session.rollback.assert_called_once_with()
