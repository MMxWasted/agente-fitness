from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserPublic

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserPublic:
    return UserPublic.model_validate(current_user)
