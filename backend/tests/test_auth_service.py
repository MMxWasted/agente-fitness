from secrets import token_urlsafe
from unittest.mock import Mock

import pytest
from pydantic import SecretStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import UserRegistration
from app.services import auth as auth_service
from app.services.auth import (
    EmailAlreadyRegisteredError,
    InvalidEmailError,
    normalize_email,
    register_user,
)


def test_email_is_trimmed_and_normalized_for_identity_comparison() -> None:
    assert normalize_email("  Person.Name+tag@EXAMPLE.COM  ") == (
        "person.name+tag@example.com"
    )


def test_invalid_email_cannot_be_normalized() -> None:
    with pytest.raises(InvalidEmailError):
        normalize_email("not-an-email")


def test_registration_rejects_an_existing_normalized_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock(spec=Session)
    existing_user = User(
        email="person@example.com",
        password_hash="stored-hash",
        is_active=True,
    )
    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        lambda _session, _email: existing_user,
    )
    registration = UserRegistration(
        email="Person@Example.com",
        password=SecretStr(token_urlsafe(32)),
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        register_user(session, registration)

    session.add.assert_not_called()


def test_unique_constraint_race_is_reported_as_duplicate_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock(spec=Session)

    class Diagnostics:
        constraint_name = "uq_users_email"

    class OriginalDatabaseError(Exception):
        diag = Diagnostics()

    session.commit.side_effect = IntegrityError(
        "INSERT INTO users",
        {},
        OriginalDatabaseError(),
    )
    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        lambda _session, _email: None,
    )
    registration = UserRegistration(
        email="person@example.com",
        password=SecretStr(token_urlsafe(32)),
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        register_user(session, registration)

    session.rollback.assert_called_once_with()
