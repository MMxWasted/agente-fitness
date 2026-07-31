import json
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.config import get_settings
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.auth import ErrorResponse
from app.schemas.body_measurement_history import (
    BodyMeasurementImportDecisions,
    BodyMeasurementImportList,
    BodyMeasurementImportPlan,
    BodyMeasurementImportPublic,
)
from app.schemas.body_measurement_import import BodyMeasurementImportPreview
from app.services.body_measurement_history import (
    BodyMeasurementConflictError,
    BodyMeasurementResourceNotFoundError,
    BodyMeasurementValidationError,
    confirm_import,
    plan_import,
    read_import,
    read_imports,
    revert_import,
)
from app.services.body_measurement_imports.preparation import (
    InvalidImportDecisionError,
)
from app.services.body_measurement_imports.workbook import (
    BodyMeasurementWorkbookAdapterV1,
    InvalidWorkbookError,
    UnsupportedWorkbookError,
    UploadTooLargeError,
    WorkbookPolicy,
    validate_xlsx_archive,
)

router = APIRouter(
    prefix="/api/v1/body-measurement-imports",
    tags=["body measurement imports"],
)

_error_responses: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Missing or invalid bearer token",
    },
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": "Inactive account",
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "Owned resource not found",
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "Workbook, history, version, or idempotency conflict",
    },
    status.HTTP_413_CONTENT_TOO_LARGE: {
        "model": ErrorResponse,
        "description": "The uploaded file exceeds the configured size limit",
    },
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
        "model": ErrorResponse,
        "description": "The upload is not a supported macro-free XLSX file",
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ErrorResponse,
        "description": "The request, decisions, or workbook are invalid",
    },
}


@router.post(
    "/preview",
    response_model=BodyMeasurementImportPreview,
    responses=_error_responses,
    summary="Preview a known body-measurement XLSX format",
    description=(
        "Authenticates the current user, validates a macro-free XLSX package, "
        "and returns a normalized preview. The original workbook and preview "
        "are not persisted."
    ),
)
async def preview_body_measurement_import(
    file: Annotated[
        UploadFile,
        File(description="Macro-free .xlsx workbook in the supported V1 format"),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BodyMeasurementImportPreview:
    del current_user
    _, preview = await _read_workbook(file)
    return preview


@router.post(
    "/plan",
    response_model=BodyMeasurementImportPlan,
    responses=_error_responses,
    summary="Classify a body-measurement import without persisting measurements",
)
async def plan_body_measurement_import(
    file: Annotated[UploadFile, File(description="The same workbook previewed")],
    source_id: Annotated[UUID, Form()],
    preview_fingerprint: Annotated[
        str,
        Form(pattern=r"^sha256:[0-9a-f]{64}$"),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
    decisions: Annotated[
        str,
        Form(
            description=(
                "JSON encoded BodyMeasurementImportDecisions. Ownership and "
                "measurement values are not client-controlled."
            )
        ),
    ] = "{}",
) -> BodyMeasurementImportPlan:
    _, preview = await _read_workbook(file)
    if preview.fingerprint != preview_fingerprint:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Workbook preview changed",
        )
    parsed_decisions = _parse_decisions(decisions)
    try:
        return plan_import(
            session,
            current_user,
            source_id=source_id,
            preview=preview,
            decisions=parsed_decisions,
        )
    except BodyMeasurementResourceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        ) from error
    except InvalidImportDecisionError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid import decisions",
        ) from error


@router.post(
    "",
    response_model=BodyMeasurementImportPublic,
    status_code=status.HTTP_201_CREATED,
    responses=_error_responses,
    summary="Confirm a planned body-measurement import",
    description=(
        "Reanalyses the workbook, locks the owned source, validates its history "
        "version, and persists normalized values atomically. Idempotency-Key "
        "must contain 16 to 128 safe ASCII characters. Replaying the same key "
        "and request returns 200 with the prior result; reusing it for another "
        "request returns 409."
    ),
)
async def confirm_body_measurement_import(
    response: Response,
    file: Annotated[UploadFile, File(description="The same workbook planned")],
    source_id: Annotated[UUID, Form()],
    preview_fingerprint: Annotated[
        str,
        Form(pattern=r"^sha256:[0-9a-f]{64}$"),
    ],
    confirmed_fingerprint: Annotated[
        str,
        Form(pattern=r"^sha256:[0-9a-f]{64}$"),
    ],
    history_version: Annotated[int, Form(ge=0)],
    idempotency_key: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            min_length=16,
            max_length=128,
            pattern=r"^[A-Za-z0-9._~-]+$",
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
    decisions: Annotated[str, Form()] = "{}",
) -> BodyMeasurementImportPublic:
    content, preview = await _read_workbook(file)
    parsed_decisions = _parse_decisions(decisions)
    try:
        result = confirm_import(
            session,
            current_user,
            source_id=source_id,
            content=content,
            preview=preview,
            preview_fingerprint=preview_fingerprint,
            confirmed_fingerprint=confirmed_fingerprint,
            history_version=history_version,
            decisions=parsed_decisions,
            idempotency_key=idempotency_key,
        )
    except BodyMeasurementResourceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        ) from error
    except BodyMeasurementConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except (BodyMeasurementValidationError, InvalidImportDecisionError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid or blocked import plan",
        ) from error
    if result.replayed:
        response.status_code = status.HTTP_200_OK
    return result.measurement_import


@router.get(
    "",
    response_model=BodyMeasurementImportList,
    responses=_error_responses,
    summary="List owned body-measurement imports",
)
def list_imports(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
    source_id: UUID | None = None,
    import_status: Annotated[
        Literal["completed", "reverted"] | None,
        Query(alias="status"),
    ] = None,
    imported_from: datetime | None = None,
    imported_to: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> BodyMeasurementImportList:
    try:
        return read_imports(
            session,
            current_user,
            source_id=source_id,
            status=import_status,
            imported_from=imported_from,
            imported_to=imported_to,
            limit=limit,
            offset=offset,
        )
    except BodyMeasurementValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid import filters",
        ) from error


@router.get(
    "/{import_id}",
    response_model=BodyMeasurementImportPublic,
    responses=_error_responses,
    summary="Read an owned body-measurement import",
)
def get_import(
    import_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
) -> BodyMeasurementImportPublic:
    try:
        return read_import(session, current_user, import_id)
    except BodyMeasurementResourceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import not found",
        ) from error


@router.delete(
    "/{import_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=_error_responses,
    summary="Revert an owned body-measurement import",
    description=(
        "Atomically removes reviews created by the import and restores safe "
        "predecessors. Repeating an already completed reversal returns 204; a "
        "later dependent version returns 409."
    ),
)
def delete_import(
    import_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
) -> Response:
    try:
        revert_import(session, current_user, import_id)
    except BodyMeasurementResourceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import not found",
        ) from error
    except BodyMeasurementConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _read_workbook(
    file: UploadFile,
) -> tuple[bytes, BodyMeasurementImportPreview]:
    settings = get_settings()
    policy = WorkbookPolicy(
        max_file_size_bytes=settings.body_measurement_upload_max_bytes,
        max_zip_entries=settings.body_measurement_zip_max_entries,
        max_uncompressed_size_bytes=(
            settings.body_measurement_zip_max_uncompressed_bytes
        ),
    )
    try:
        content = await file.read(policy.max_file_size_bytes + 1)
        if len(content) > policy.max_file_size_bytes:
            raise UploadTooLargeError("The uploaded file exceeds the configured limit")
        archive_metadata = validate_xlsx_archive(
            content,
            filename=file.filename,
            content_type=file.content_type,
            policy=policy,
        )
        preview = BodyMeasurementWorkbookAdapterV1().preview(
            content,
            archive_metadata=archive_metadata,
        )
        return content, preview
    except UploadTooLargeError as error:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(error),
        ) from error
    except UnsupportedWorkbookError as error:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(error),
        ) from error
    except InvalidWorkbookError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    finally:
        await file.close()


def _parse_decisions(value: str) -> BodyMeasurementImportDecisions:
    try:
        raw = json.loads(value)
        return BodyMeasurementImportDecisions.model_validate(raw)
    except (json.JSONDecodeError, ValidationError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid import decisions",
        ) from error
