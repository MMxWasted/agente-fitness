from datetime import date
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.auth import ErrorResponse
from app.schemas.body_measurement_history import (
    BodyMeasurementReviewDetail,
    BodyMeasurementReviewList,
)
from app.services.body_measurement_history import (
    BodyMeasurementResourceNotFoundError,
    BodyMeasurementValidationError,
    read_review,
    read_reviews,
)

router = APIRouter(
    prefix="/api/v1/body-measurement-reviews",
    tags=["body measurement reviews"],
)

_responses: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
}


@router.get("", response_model=BodyMeasurementReviewList, responses=_responses)
def list_reviews(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
    source_id: UUID | None = None,
    measured_from: date | None = None,
    measured_to: date | None = None,
    current: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> BodyMeasurementReviewList:
    try:
        return read_reviews(
            session,
            current_user,
            source_id=source_id,
            measured_from=measured_from,
            measured_to=measured_to,
            current=current,
            limit=limit,
            offset=offset,
        )
    except BodyMeasurementValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid review filters",
        ) from error


@router.get(
    "/{review_id}",
    response_model=BodyMeasurementReviewDetail,
    responses=_responses,
)
def get_review(
    review_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
) -> BodyMeasurementReviewDetail:
    try:
        return read_review(session, current_user, review_id)
    except BodyMeasurementResourceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        ) from error
