from pydantic import EmailStr, SecretStr, TypeAdapter, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    perform_dummy_password_verification,
    verify_password_and_update,
)
from app.models.user import User
from app.repositories.user import add_user, get_user_by_email
from app.schemas.auth import UserRegistration

_email_adapter = TypeAdapter(EmailStr)
_user_email_unique_constraint = "uq_users_email"


class InvalidEmailError(ValueError):
    """Raised when a login identifier is not a valid email address."""


class EmailAlreadyRegisteredError(ValueError):
    """Raised when a normalized email already identifies an account."""


def normalize_email(email: str) -> str:
    try:
        validated_email = _email_adapter.validate_python(email.strip())
    except ValidationError as error:
        raise InvalidEmailError from error

    return str(validated_email).casefold()


def register_user(
    session: Session,
    registration: UserRegistration,
) -> User:
    normalized_email = normalize_email(str(registration.email))
    if get_user_by_email(session, normalized_email) is not None:
        raise EmailAlreadyRegisteredError

    user = User(
        email=normalized_email,
        password_hash=hash_password(registration.password),
        is_active=True,
    )
    add_user(session, user)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        if _get_constraint_name(error) == _user_email_unique_constraint:
            raise EmailAlreadyRegisteredError from error
        raise

    session.refresh(user)
    return user


def authenticate_user(
    session: Session,
    email: str,
    password: SecretStr,
) -> User | None:
    password_value = password.get_secret_value()
    if not 15 <= len(password_value) <= 128:
        return None

    try:
        normalized_email = normalize_email(email)
    except InvalidEmailError:
        perform_dummy_password_verification(password)
        return None

    user = get_user_by_email(session, normalized_email)
    if user is None:
        perform_dummy_password_verification(password)
        return None

    verified, updated_hash = verify_password_and_update(
        password,
        user.password_hash,
    )
    if not verified or not user.is_active:
        return None

    if updated_hash is not None:
        user.password_hash = updated_hash
        session.commit()

    return user


def _get_constraint_name(error: IntegrityError) -> str | None:
    original_error = error.orig
    diagnostics = getattr(original_error, "diag", None)
    constraint_name = getattr(diagnostics, "constraint_name", None)
    return constraint_name if isinstance(constraint_name, str) else None
