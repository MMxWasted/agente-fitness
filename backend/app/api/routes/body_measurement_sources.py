from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.auth import ErrorResponse
from app.schemas.body_measurement_history import (
    BodyMeasurementSourceCreate,
    BodyMeasurementSourceList,
    BodyMeasurementSourcePublic,
)
from app.services.body_measurement_history import (
    BodyMeasurementConflictError,
    create_source,
    read_sources,
)

router = APIRouter(
    prefix="/api/v1/body-measurement-sources",
    tags=["body measurement sources"],
)

_responses: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "The logical source key already exists",
    },
}


@router.get("", response_model=BodyMeasurementSourceList, responses=_responses)
def list_sources(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> BodyMeasurementSourceList:
    return read_sources(
        session,
        current_user,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=BodyMeasurementSourcePublic,
    status_code=status.HTTP_201_CREATED,
    responses=_responses,
)
def create_measurement_source(
    source_data: BodyMeasurementSourceCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
) -> BodyMeasurementSourcePublic:
    try:
        return create_source(session, current_user, source_data)
    except BodyMeasurementConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Source logical key already exists",
        ) from error
