from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import SecretStr
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.cookies import clear_refresh_cookie, set_refresh_cookie
from app.core.csrf import InvalidCsrfOriginError, validate_request_origin
from app.db.session import get_db_session
from app.schemas.auth import ErrorResponse, TokenResponse, UserRegistration
from app.schemas.user import UserPublic
from app.services.auth import (
    EmailAlreadyRegisteredError,
    authenticate_user,
    register_user,
)
from app.services.session import (
    InvalidSessionError,
    create_user_session,
    revoke_user_session,
    rotate_user_session,
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
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Untrusted browser origin",
        },
    },
)
def login_for_access_token(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_db_session)],
) -> TokenResponse:
    _enforce_request_origin(request, required=False)
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

    settings = get_settings()
    credentials = create_user_session(session, user, settings=settings)
    set_refresh_cookie(
        response,
        credentials.refresh_token,
        credentials.refresh_expires_at,
        settings=settings,
    )
    return TokenResponse(
        access_token=credentials.access_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Invalid session credential",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Missing or untrusted browser origin",
        },
    },
)
def refresh_access_token(
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
) -> TokenResponse:
    _enforce_request_origin(request, required=True)
    settings = get_settings()
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_token:
        raise _invalid_session_exception()

    try:
        credentials = rotate_user_session(
            session,
            refresh_token,
            settings=settings,
        )
    except InvalidSessionError as error:
        raise _invalid_session_exception() from error

    set_refresh_cookie(
        response,
        credentials.refresh_token,
        credentials.refresh_expires_at,
        settings=settings,
    )
    return TokenResponse(
        access_token=credentials.access_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "Missing or untrusted browser origin",
        }
    },
)
def logout(
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> Response:
    _enforce_request_origin(request, required=True)
    settings = get_settings()
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    revoke_user_session(session, refresh_token)

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_refresh_cookie(response, settings=settings)
    return response


def _enforce_request_origin(request: Request, *, required: bool) -> None:
    try:
        validate_request_origin(
            request.headers.get("origin"),
            required=required,
        )
    except InvalidCsrfOriginError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Request origin is not allowed",
        ) from error


def _invalid_session_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not refresh session",
        headers={"WWW-Authenticate": "Bearer"},
    )
