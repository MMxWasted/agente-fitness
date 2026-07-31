from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_profile import UserProfile
from app.repositories.user_profile import (
    add_user_profile,
    get_user_profile_by_user_id,
)
from app.schemas.profile import ProfileUpsert

_user_profile_unique_constraint = "uq_user_profiles_user_id"


def get_user_profile(
    session: Session,
    user: User,
) -> UserProfile | None:
    return get_user_profile_by_user_id(session, user.id)


def put_user_profile(
    session: Session,
    user: User,
    profile_data: ProfileUpsert,
) -> UserProfile:
    profile = get_user_profile_by_user_id(session, user.id)
    if profile is None:
        profile = UserProfile(user_id=user.id)
        _replace_profile(profile, profile_data)
        add_user_profile(session, profile)
        try:
            session.commit()
        except IntegrityError as error:
            session.rollback()
            if _get_constraint_name(error) != _user_profile_unique_constraint:
                raise
            profile = get_user_profile_by_user_id(session, user.id)
            if profile is None:
                raise
            if not _replace_profile(profile, profile_data):
                return profile
            _commit_profile(session)
    elif _replace_profile(profile, profile_data):
        _commit_profile(session)

    session.refresh(profile)
    return profile


def _replace_profile(
    profile: UserProfile,
    profile_data: ProfileUpsert,
) -> bool:
    values = profile_data.model_dump()
    changed = any(
        getattr(profile, field_name, None) != value
        for field_name, value in values.items()
    )
    if changed:
        for field_name, value in values.items():
            setattr(profile, field_name, value)
    return changed


def _commit_profile(session: Session) -> None:
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise


def _get_constraint_name(error: IntegrityError) -> str | None:
    diagnostics = getattr(error.orig, "diag", None)
    constraint_name = getattr(diagnostics, "constraint_name", None)
    return constraint_name if isinstance(constraint_name, str) else None
