from typing import Annotated, Literal

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.readiness import is_database_ready
from app.db.session import get_db_session

router = APIRouter(tags=["readiness"])


class ReadinessResponse(BaseModel):
    status: Literal["ready"]


class ReadinessUnavailableResponse(BaseModel):
    status: Literal["unavailable"]


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ReadinessUnavailableResponse,
            "description": "Database unavailable",
        }
    },
)
def readiness(
    session: Annotated[Session, Depends(get_db_session)],
) -> ReadinessResponse | JSONResponse:
    if not is_database_ready(session):
        response = ReadinessUnavailableResponse(status="unavailable")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response.model_dump(),
        )

    return ReadinessResponse(status="ready")
