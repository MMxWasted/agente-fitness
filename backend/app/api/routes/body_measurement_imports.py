from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies.auth import get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.schemas.auth import ErrorResponse
from app.schemas.body_measurement_import import BodyMeasurementImportPreview
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
        "description": "The multipart request or workbook structure is invalid",
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
    settings = get_settings()
    policy = WorkbookPolicy(
        max_file_size_bytes=settings.body_measurement_upload_max_bytes,
        max_zip_entries=settings.body_measurement_zip_max_entries,
        max_uncompressed_size_bytes=(
            settings.body_measurement_zip_max_uncompressed_bytes
        ),
    )
    del current_user

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
        return BodyMeasurementWorkbookAdapterV1().preview(
            content,
            archive_metadata=archive_metadata,
        )
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
