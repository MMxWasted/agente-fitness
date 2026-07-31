from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.user_profile import UserProfile
from app.schemas.profile import ProfileUpsert


def valid_profile_data() -> dict[str, object]:
    return {
        "display_name": "Alex",
        "birth_date": date(1995, 5, 12),
        "height_cm": Decimal("178.25"),
        "experience_level": "intermediate",
        "timezone": "Europe/Madrid",
        "unit_system": "metric",
    }


def test_profile_normalizes_display_name_and_accepts_valid_values() -> None:
    data = valid_profile_data()
    data["display_name"] = "  Alex Fitness  "

    profile = ProfileUpsert.model_validate(data)

    assert profile.display_name == "Alex Fitness"
    assert profile.birth_date == date(1995, 5, 12)
    assert profile.height_cm == Decimal("178.25")


@pytest.mark.parametrize("display_name", ["", "   ", "x" * 81])
def test_profile_rejects_invalid_display_name(display_name: str) -> None:
    data = valid_profile_data()
    data["display_name"] = display_name

    with pytest.raises(ValidationError):
        ProfileUpsert.model_validate(data)


def test_profile_accepts_a_valid_birth_date_and_rejects_a_future_date() -> None:
    valid_data = valid_profile_data()
    valid_data["birth_date"] = date(2000, 1, 1)
    assert ProfileUpsert.model_validate(valid_data).birth_date == date(2000, 1, 1)

    invalid_data = valid_profile_data()
    invalid_data["birth_date"] = datetime.now(UTC).date() + timedelta(days=1)
    with pytest.raises(ValidationError):
        ProfileUpsert.model_validate(invalid_data)


@pytest.mark.parametrize(
    "height_cm",
    [Decimal("0.01"), Decimal("180"), Decimal("300")],
)
def test_profile_accepts_valid_heights(height_cm: Decimal) -> None:
    data = valid_profile_data()
    data["height_cm"] = height_cm

    assert ProfileUpsert.model_validate(data).height_cm == height_cm


@pytest.mark.parametrize(
    "height_cm",
    [
        Decimal("0"),
        Decimal("-1"),
        Decimal("300.01"),
        Decimal("NaN"),
        Decimal("Infinity"),
        True,
        False,
    ],
)
def test_profile_rejects_invalid_heights(height_cm: object) -> None:
    data = valid_profile_data()
    data["height_cm"] = height_cm

    with pytest.raises(ValidationError):
        ProfileUpsert.model_validate(data)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("experience_level", "expert"),
        ("timezone", "Mars/Olympus"),
        ("unit_system", "stone"),
    ],
)
def test_profile_rejects_invalid_closed_values(
    field_name: str,
    invalid_value: str,
) -> None:
    data = valid_profile_data()
    data[field_name] = invalid_value

    with pytest.raises(ValidationError):
        ProfileUpsert.model_validate(data)


def test_profile_accepts_iana_timezones_and_both_unit_systems() -> None:
    utc_profile = valid_profile_data()
    utc_profile["timezone"] = "UTC"
    utc_profile["unit_system"] = "imperial"

    profile = ProfileUpsert.model_validate(utc_profile)

    assert profile.timezone == "UTC"
    assert profile.unit_system == "imperial"


@pytest.mark.parametrize(
    "internal_field",
    ["id", "user_id", "created_at", "updated_at"],
)
def test_profile_rejects_internal_and_additional_fields(
    internal_field: str,
) -> None:
    data = valid_profile_data()
    data[internal_field] = str(uuid4())

    with pytest.raises(ValidationError):
        ProfileUpsert.model_validate(data)


def test_profile_put_semantics_clear_omitted_optional_values() -> None:
    profile = ProfileUpsert.model_validate(
        {
            "display_name": "Alex",
            "experience_level": "beginner",
            "timezone": "UTC",
            "unit_system": "metric",
        }
    )

    assert profile.birth_date is None
    assert profile.height_cm is None


def test_profile_requires_context_fields_without_guessing_defaults() -> None:
    for missing_field in (
        "display_name",
        "experience_level",
        "timezone",
        "unit_system",
    ):
        data = valid_profile_data()
        data.pop(missing_field)

        with pytest.raises(ValidationError):
            ProfileUpsert.model_validate(data)


def test_profile_representation_contains_only_technical_identifiers() -> None:
    profile = UserProfile(
        id=uuid4(),
        user_id=uuid4(),
        display_name="Private display name",
        birth_date=date(1995, 5, 12),
        height_cm=Decimal("178.25"),
        experience_level="intermediate",
        timezone="Europe/Madrid",
        unit_system="metric",
    )

    representation = repr(profile)

    assert "Private display name" not in representation
    assert "1995" not in representation
    assert "178.25" not in representation
