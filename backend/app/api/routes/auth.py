from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import SecretStr
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import get_db_session
from app.schemas.auth import ErrorResponse, TokenResponse, UserRegistration
from app.schemas.user import UserPublic
from app.services.auth import (
    EmailAlreadyRegisteredError,
    authenticate_user,
    register_user,
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Email already registered",
        }
    },
)
def register_account(
    registration: UserRegistration,
    session: Annotated[Session, Depends(get_db_session)],
) -> UserPublic:
    try:
        user = register_user(session, registration)
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from error

    return UserPublic.model_validate(user)


@router.post(
    "/token",
    response_model=TokenResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Invalid credentials",
        }
    },
)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_db_session)],
) -> TokenResponse:
    user = authenticate_user(
        session,
        email=form_data.username,
        password=SecretStr(form_data.password),
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=create_access_token(user.id))
