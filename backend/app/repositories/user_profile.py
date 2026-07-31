from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_profile import UserProfile


def get_user_profile_by_user_id(
    session: Session,
    user_id: UUID,
) -> UserProfile | None:
    return session.scalar(select(UserProfile).where(UserProfile.user_id == user_id))


def add_user_profile(
    session: Session,
    profile: UserProfile,
) -> None:
    session.add(profile)
