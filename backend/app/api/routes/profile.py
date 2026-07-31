from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.auth import ErrorResponse
from app.schemas.profile import ProfilePublic, ProfileUpsert
from app.services.profile import get_user_profile, put_user_profile

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])

_authentication_responses: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Missing or invalid bearer token",
    },
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": "Inactive account",
    },
}


@router.get(
    "",
    response_model=ProfilePublic,
    responses={
        **_authentication_responses,
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Profile not created yet",
        },
    },
)
def read_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
) -> ProfilePublic:
    profile = get_user_profile(session, current_user)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return ProfilePublic.model_validate(profile)


@router.put(
    "",
    response_model=ProfilePublic,
    responses=_authentication_responses,
)
def replace_profile(
    profile_data: ProfileUpsert,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
) -> ProfilePublic:
    profile = put_user_profile(session, current_user, profile_data)
    return ProfilePublic.model_validate(profile)
