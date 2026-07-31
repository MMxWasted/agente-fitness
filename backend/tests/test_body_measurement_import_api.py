from collections.abc import Callable, Generator
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response  # type: ignore[import-untyped]
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.models.user import User

client = TestClient(app)
NOW = datetime(2026, 7, 30, 12, tzinfo=UTC)
FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "body_measurements"
    / "body_measurements_format_v1.xlsx"
)
XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def build_user(*, is_active: bool = True) -> User:
    return User(
        id=uuid4(),
        email="person@example.com",
        password_hash="opaque-password-hash",
        is_active=is_active,
        created_at=NOW,
        updated_at=NOW,
    )


def build_session_override(
    session: Session,
) -> Callable[[], Generator[Session]]:
    def override_session() -> Generator[Session]:
        yield session

    return override_session


def upload_fixture(
    *,
    filename: str = "synthetic-measurements.xlsx",
    content: bytes | None = None,
    content_type: str = XLSX_CONTENT_TYPE,
) -> Response:
    return client.post(
        "/api/v1/body-measurement-imports/preview",
        files={
            "file": (
                filename,
                content or FIXTURE.read_bytes(),
                content_type,
            )
        },
    )


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Generator[None]:
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_preview_requires_a_valid_active_bearer_identity() -> None:
    missing_response = upload_fixture()

    session = Mock(spec=Session)
    inactive_user = build_user(is_active=False)
    session.get.return_value = inactive_user
    app.dependency_overrides[get_db_session] = build_session_override(session)
    invalid_response = client.post(
        "/api/v1/body-measurement-imports/preview",
        headers={"Authorization": "Bearer invalid"},
        files={
            "file": (
                "measurements.xlsx",
                FIXTURE.read_bytes(),
                XLSX_CONTENT_TYPE,
            )
        },
    )
    inactive_response = client.post(
        "/api/v1/body-measurement-imports/preview",
        headers={"Authorization": f"Bearer {create_access_token(inactive_user.id)}"},
        files={
            "file": (
                "measurements.xlsx",
                FIXTURE.read_bytes(),
                XLSX_CONTENT_TYPE,
            )
        },
    )

    assert missing_response.status_code == 401
    assert invalid_response.status_code == 401
    assert inactive_response.status_code == 403


def test_preview_returns_safe_normalized_content_without_persistence() -> None:
    app.dependency_overrides[get_current_user] = build_user

    response = upload_fixture(filename="private-person-name.xlsx")

    assert response.status_code == 200
    payload = response.json()
    assert payload["adapter_version"] == "body-measurements-v1"
    assert payload["fingerprint"].startswith("sha256:")
    assert payload["totals"]["revision_count"] == 3
    assert payload["totals"]["has_blocking_errors"] is True
    assert payload["revisions"][1]["raw_date"] == "06-03"
    assert "user_id" not in response.text
    assert "private-person-name" not in response.text
    assert "access_token" not in response.text
    assert not any("measurement" in table_name for table_name in Base.metadata.tables)


def test_preview_rejects_invalid_multipart_format_and_content() -> None:
    app.dependency_overrides[get_current_user] = build_user

    missing_file_response = client.post("/api/v1/body-measurement-imports/preview")
    format_response = upload_fixture(filename="measurements.csv")
    invalid_content_response = upload_fixture(
        content=b"arbitrary-sensitive-cell-content",
    )

    assert missing_file_response.status_code == 422
    assert format_response.status_code == 415
    assert invalid_content_response.status_code == 415
    assert "arbitrary-sensitive-cell-content" not in invalid_content_response.text


def test_preview_rejects_size_over_the_configured_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app.dependency_overrides[get_current_user] = build_user
    monkeypatch.setattr(
        get_settings(),
        "body_measurement_upload_max_bytes",
        100,
    )

    response = upload_fixture()

    assert response.status_code == 413
    assert response.json() == {
        "detail": "The uploaded file exceeds the configured limit"
    }


def test_openapi_documents_preview_security_and_closed_contract() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    contract = paths["/api/v1/body-measurement-imports/preview"]["post"]
    assert {"200", "401", "403", "413", "415", "422"} <= set(contract["responses"])
    assert contract["security"] == [{"OAuth2PasswordBearer": []}]
    request_schema = contract["requestBody"]["content"]["multipart/form-data"]["schema"]
    assert "user_id" not in str(request_schema)

    response_schema = response.json()["components"]["schemas"][
        "BodyMeasurementImportPreview"
    ]
    assert "user_id" not in str(response_schema)
    assert "/health" in paths
    assert "/ready" in paths
    assert "/api/v1/profile" in paths
