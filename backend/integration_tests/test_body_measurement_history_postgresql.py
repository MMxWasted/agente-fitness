import json
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from secrets import token_urlsafe
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook  # type: ignore[import-untyped]
from sqlalchemy import delete, func, inspect, select, text

from app.db.session import get_engine, get_session_factory
from app.main import app
from app.models.body_measurement import (
    BodyMeasurementImport,
    BodyMeasurementReview,
    BodyMeasurementSource,
    BodyMeasurementValue,
)
from app.models.user import User

pytestmark = pytest.mark.integration

FIXTURE = (
    Path(__file__).parents[1]
    / "tests"
    / "fixtures"
    / "body_measurements"
    / "body_measurements_format_v1.xlsx"
)
XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@pytest.fixture
def client() -> Generator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def created_emails() -> Generator[list[str]]:
    emails: list[str] = []
    yield emails
    if emails:
        with get_session_factory()() as session:
            session.execute(delete(User).where(User.email.in_(set(emails))))
            session.commit()


def register_and_login(
    client: TestClient,
    created_emails: list[str],
    *,
    prefix: str,
) -> tuple[UUID, str]:
    email = f"{prefix}-{uuid4()}@example.com"
    password = token_urlsafe(32)
    created_emails.append(email)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    token_response = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    assert token_response.status_code == 200
    return UUID(response.json()["id"]), token_response.json()["access_token"]


def authorization(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def create_source(client: TestClient, token: str, suffix: str) -> dict[str, object]:
    response = client.post(
        "/api/v1/body-measurement-sources",
        headers=authorization(token),
        json={
            "display_name": "Revisiones de plicometría",
            "logical_key": f"excel-{suffix}",
        },
    )
    assert response.status_code == 201
    return response.json()


def preview_workbook(
    client: TestClient,
    token: str,
    content: bytes,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/body-measurement-imports/preview",
        headers=authorization(token),
        files={"file": ("measurements.xlsx", content, XLSX_CONTENT_TYPE)},
    )
    assert response.status_code == 200
    return response.json()


def decisions_for(preview: dict[str, object]) -> dict[str, object]:
    unknown_metrics = preview["unknown_metrics"]
    assert isinstance(unknown_metrics, list)
    return {
        "date_resolutions": [{"revision_index": 1, "measurement_date": "2026-03-06"}],
        "excluded_unknown_metrics": [
            {
                "category_label": item["category_label"],
                "original_label": item["original_label"],
                "side": item["side"],
            }
            for item in unknown_metrics
        ],
    }


def plan_workbook(
    client: TestClient,
    token: str,
    *,
    source_id: str,
    content: bytes,
    preview: dict[str, object],
    decisions: dict[str, object],
) -> dict[str, object]:
    response = client.post(
        "/api/v1/body-measurement-imports/plan",
        headers=authorization(token),
        data={
            "source_id": source_id,
            "preview_fingerprint": preview["fingerprint"],
            "decisions": json.dumps(decisions),
        },
        files={"file": ("measurements.xlsx", content, XLSX_CONTENT_TYPE)},
    )
    assert response.status_code == 200, response.text
    return response.json()


def confirm_workbook(
    client: TestClient,
    token: str,
    *,
    source_id: str,
    content: bytes,
    preview: dict[str, object],
    plan: dict[str, object],
    decisions: dict[str, object],
    idempotency_key: str,
):
    return client.post(
        "/api/v1/body-measurement-imports",
        headers={
            **authorization(token),
            "Idempotency-Key": idempotency_key,
        },
        data={
            "source_id": source_id,
            "preview_fingerprint": preview["fingerprint"],
            "confirmed_fingerprint": plan["confirmed_fingerprint"],
            "history_version": plan["history_version"],
            "decisions": json.dumps(decisions),
        },
        files={"file": ("measurements.xlsx", content, XLSX_CONTENT_TYPE)},
    )


def workbook_with_change(cell_reference: str, value: object) -> bytes:
    workbook = load_workbook(FIXTURE, data_only=False, keep_links=False)
    workbook["Revisiones"][cell_reference] = value
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def test_migration_defines_private_normalized_history_constraints() -> None:
    inspector = inspect(get_engine())
    assert {
        "body_measurement_sources",
        "body_measurement_imports",
        "body_measurement_reviews",
        "body_measurement_values",
    } <= set(inspector.get_table_names())

    value_columns = {
        item["name"]: item for item in inspector.get_columns("body_measurement_values")
    }
    assert value_columns["value"]["type"].precision == 14
    assert value_columns["value"]["type"].scale == 6
    assert value_columns["created_at"]["type"].timezone

    review_indexes = {
        item["name"]: item for item in inspector.get_indexes("body_measurement_reviews")
    }
    assert review_indexes["uq_body_measurement_reviews_current_identity"]["unique"]
    assert "is_current" in str(
        review_indexes["uq_body_measurement_reviews_current_identity"][
            "dialect_options"
        ]
    )

    import_uniques = {
        item["name"]: set(item["column_names"])
        for item in inspector.get_unique_constraints("body_measurement_imports")
    }
    assert import_uniques["uq_body_measurement_imports_user_idempotency_key"] == {
        "user_id",
        "idempotency_key_hash",
    }
    with get_engine().connect() as connection:
        revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
    assert revision == "20260731_0005"


def test_import_version_replay_visibility_and_reversal_flow(
    client: TestClient,
    created_emails: list[str],
) -> None:
    first_user_id, first_token = register_and_login(
        client, created_emails, prefix="measurements-owner"
    )
    second_user_id, second_token = register_and_login(
        client, created_emails, prefix="measurements-other"
    )
    assert client.get("/api/v1/body-measurement-sources").status_code == 401
    assert (
        client.get(
            "/api/v1/body-measurement-sources",
            headers=authorization("not-a-valid-token"),
        ).status_code
        == 401
    )
    source = create_source(client, first_token, uuid4().hex)
    source_id = str(source["id"])
    content = FIXTURE.read_bytes()
    preview = preview_workbook(client, first_token, content)
    decisions = decisions_for(preview)
    changed_fingerprint = client.post(
        "/api/v1/body-measurement-imports/plan",
        headers=authorization(first_token),
        data={
            "source_id": source_id,
            "preview_fingerprint": f"sha256:{'0' * 64}",
            "decisions": json.dumps(decisions),
        },
        files={"file": ("measurements.xlsx", content, XLSX_CONTENT_TYPE)},
    )
    assert changed_fingerprint.status_code == 409
    assert "sha256:" not in changed_fingerprint.text
    foreign_source = client.post(
        "/api/v1/body-measurement-imports/plan",
        headers=authorization(second_token),
        data={
            "source_id": source_id,
            "preview_fingerprint": preview["fingerprint"],
            "decisions": json.dumps(decisions),
        },
        files={"file": ("measurements.xlsx", content, XLSX_CONTENT_TYPE)},
    )
    assert foreign_source.status_code == 404
    plan = plan_workbook(
        client,
        first_token,
        source_id=source_id,
        content=content,
        preview=preview,
        decisions=decisions,
    )
    assert plan["totals"] == {
        "new": 3,
        "identical": 0,
        "modified": 0,
        "blocked": 0,
        "excluded": 0,
    }

    first = confirm_workbook(
        client,
        first_token,
        source_id=source_id,
        content=content,
        preview=preview,
        plan=plan,
        decisions=decisions,
        idempotency_key="first-import-key-0001",
    )
    replay = confirm_workbook(
        client,
        first_token,
        source_id=source_id,
        content=content,
        preview=preview,
        plan=plan,
        decisions=decisions,
        idempotency_key="first-import-key-0001",
    )
    assert first.status_code == 201
    assert replay.status_code == 200
    assert replay.json() == first.json()

    stale_history = confirm_workbook(
        client,
        first_token,
        source_id=source_id,
        content=content,
        preview=preview,
        plan=plan,
        decisions=decisions,
        idempotency_key="stale-history-key-0009",
    )
    assert stale_history.status_code == 409
    assert stale_history.json() == {"detail": "Measurement history changed"}

    reused_key = dict(plan)
    reused_key["history_version"] = 1
    conflict = confirm_workbook(
        client,
        first_token,
        source_id=source_id,
        content=content,
        preview=preview,
        plan=reused_key,
        decisions=decisions,
        idempotency_key="first-import-key-0001",
    )
    assert conflict.status_code == 409

    identical_plan = plan_workbook(
        client,
        first_token,
        source_id=source_id,
        content=content,
        preview=preview,
        decisions=decisions,
    )
    assert identical_plan["totals"]["identical"] == 3
    identical = confirm_workbook(
        client,
        first_token,
        source_id=source_id,
        content=content,
        preview=preview,
        plan=identical_plan,
        decisions=decisions,
        idempotency_key="identical-import-0002",
    )
    assert identical.status_code == 201
    assert identical.json()["outcome"] == "skipped"

    changed_content = workbook_with_change("D5", 75.25)
    changed_preview = preview_workbook(client, first_token, changed_content)
    changed_decisions = decisions_for(changed_preview)
    changed_plan = plan_workbook(
        client,
        first_token,
        source_id=source_id,
        content=changed_content,
        preview=changed_preview,
        decisions=changed_decisions,
    )
    assert changed_plan["totals"]["modified"] == 1

    rejected = confirm_workbook(
        client,
        first_token,
        source_id=source_id,
        content=changed_content,
        preview=changed_preview,
        plan=changed_plan,
        decisions=changed_decisions,
        idempotency_key="modified-reject-0003",
    )
    assert rejected.status_code == 409

    changed_decisions["modifications"] = [
        {"revision_index": 0, "action": "create_version"}
    ]
    versioned = confirm_workbook(
        client,
        first_token,
        source_id=source_id,
        content=changed_content,
        preview=changed_preview,
        plan=changed_plan,
        decisions=changed_decisions,
        idempotency_key="modified-version-0004",
    )
    assert versioned.status_code == 201, versioned.text
    assert versioned.json()["versioned_review_count"] == 1

    reviews = client.get(
        "/api/v1/body-measurement-reviews",
        headers=authorization(first_token),
        params={"source_id": source_id, "current": "false", "limit": 100},
    )
    current_reviews = client.get(
        "/api/v1/body-measurement-reviews",
        headers=authorization(first_token),
        params={"source_id": source_id, "current": "true", "limit": 100},
    )
    all_reviews = client.get(
        "/api/v1/body-measurement-reviews",
        headers=authorization(first_token),
        params={"source_id": source_id, "limit": 100},
    )
    assert reviews.status_code == current_reviews.status_code == 200
    assert reviews.json()["total"] == 1
    assert current_reviews.json()["total"] == 3
    assert all_reviews.status_code == 200
    assert all_reviews.json()["total"] == 4
    version_two = next(
        item for item in current_reviews.json()["items"] if item["version"] == 2
    )
    detail = client.get(
        f"/api/v1/body-measurement-reviews/{version_two['id']}",
        headers=authorization(first_token),
    )
    assert detail.status_code == 200
    assert any(
        value["metric_code"] == "body_weight" and value["value"] == "75.25"
        for value in detail.json()["values"]
    )

    assert (
        client.get(
            f"/api/v1/body-measurement-reviews/{version_two['id']}",
            headers=authorization(second_token),
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/body-measurement-imports/{first.json()['id']}",
            headers=authorization(second_token),
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/v1/body-measurement-imports/{first.json()['id']}",
            headers=authorization(first_token),
        ).status_code
        == 409
    )

    assert (
        client.delete(
            f"/api/v1/body-measurement-imports/{versioned.json()['id']}",
            headers=authorization(first_token),
        ).status_code
        == 204
    )
    restored = client.get(
        "/api/v1/body-measurement-reviews",
        headers=authorization(first_token),
        params={"source_id": source_id, "current": "true", "limit": 100},
    ).json()
    assert restored["total"] == 3
    assert all(item["version"] == 1 for item in restored["items"])

    assert (
        client.delete(
            f"/api/v1/body-measurement-imports/{identical.json()['id']}",
            headers=authorization(first_token),
        ).status_code
        == 204
    )
    assert (
        client.delete(
            f"/api/v1/body-measurement-imports/{first.json()['id']}",
            headers=authorization(first_token),
        ).status_code
        == 204
    )
    assert (
        client.delete(
            f"/api/v1/body-measurement-imports/{first.json()['id']}",
            headers=authorization(first_token),
        ).status_code
        == 204
    )

    with get_session_factory()() as session:
        assert (
            session.scalar(
                select(func.count(BodyMeasurementReview.id)).where(
                    BodyMeasurementReview.user_id == first_user_id
                )
            )
            == 0
        )
        assert (
            session.scalar(
                select(func.count(BodyMeasurementValue.id))
                .join(BodyMeasurementReview)
                .where(BodyMeasurementReview.user_id == first_user_id)
            )
            == 0
        )
        second_user = session.get(User, second_user_id)
        assert second_user is not None
        second_user.is_active = False
        session.commit()

    assert (
        client.get(
            "/api/v1/body-measurement-sources",
            headers=authorization(second_token),
        ).status_code
        == 403
    )


def test_partial_import_persists_only_explicitly_included_revisions(
    client: TestClient,
    created_emails: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, token = register_and_login(client, created_emails, prefix="measurements-partial")
    source = create_source(client, token, uuid4().hex)
    source_id = str(source["id"])
    duplicate_source = client.post(
        "/api/v1/body-measurement-sources",
        headers=authorization(token),
        json={
            "display_name": "Nombre alternativo",
            "logical_key": source["logical_key"],
        },
    )
    assert duplicate_source.status_code == 409
    content = FIXTURE.read_bytes()
    preview = preview_workbook(client, token, content)
    decisions = decisions_for(preview)
    decisions["excluded_revisions"] = [2]
    plan = plan_workbook(
        client,
        token,
        source_id=source_id,
        content=content,
        preview=preview,
        decisions=decisions,
    )

    assert plan["totals"]["new"] == 2
    assert plan["totals"]["excluded"] == 1

    def fail_after_import_flush(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("synthetic persistence failure")

    with monkeypatch.context() as scoped:
        scoped.setattr(
            "app.services.body_measurement_history.add_body_measurement_review",
            fail_after_import_flush,
        )
        with pytest.raises(RuntimeError, match="synthetic persistence failure"):
            confirm_workbook(
                client,
                token,
                source_id=source_id,
                content=content,
                preview=preview,
                plan=plan,
                decisions=decisions,
                idempotency_key="rollback-import-key-0011",
            )

    with get_session_factory()() as session:
        assert (
            session.scalar(
                select(func.count(BodyMeasurementImport.id)).where(
                    BodyMeasurementImport.source_id == UUID(source_id)
                )
            )
            == 0
        )
        assert (
            session.scalar(
                select(func.count(BodyMeasurementReview.id)).where(
                    BodyMeasurementReview.source_id == UUID(source_id)
                )
            )
            == 0
        )
        persisted_source = session.get(BodyMeasurementSource, UUID(source_id))
        assert persisted_source is not None
        assert persisted_source.history_version == 0

    response = confirm_workbook(
        client,
        token,
        source_id=source_id,
        content=content,
        preview=preview,
        plan=plan,
        decisions=decisions,
        idempotency_key="partial-import-key-0008",
    )
    assert response.status_code == 201
    assert response.json()["outcome"] == "partial"
    assert response.json()["created_review_count"] == 2
    assert response.json()["excluded_review_count"] == 1

    review_page = client.get(
        "/api/v1/body-measurement-reviews",
        headers=authorization(token),
        params={
            "source_id": source_id,
            "measured_from": "2026-01-01",
            "measured_to": "2026-12-31",
            "limit": 1,
            "offset": 1,
        },
    )
    import_page = client.get(
        "/api/v1/body-measurement-imports",
        headers=authorization(token),
        params={"source_id": source_id, "status": "completed", "limit": 1},
    )
    assert review_page.status_code == import_page.status_code == 200
    assert review_page.json()["total"] == 2
    assert len(review_page.json()["items"]) == 1
    assert import_page.json()["total"] == 1

    excluded_decisions = decisions_for(preview)
    excluded_decisions["excluded_revisions"] = [0, 1, 2]
    excluded_plan = plan_workbook(
        client,
        token,
        source_id=source_id,
        content=content,
        preview=preview,
        decisions=excluded_decisions,
    )
    excluded = confirm_workbook(
        client,
        token,
        source_id=source_id,
        content=content,
        preview=preview,
        plan=excluded_plan,
        decisions=excluded_decisions,
        idempotency_key="excluded-import-key-0010",
    )
    assert excluded.status_code == 201
    assert excluded.json()["outcome"] == "excluded"
    assert excluded.json()["excluded_review_count"] == 3


def test_source_lock_serializes_concurrent_idempotent_confirmation(
    client: TestClient,
    created_emails: list[str],
) -> None:
    user_id, token = register_and_login(
        client, created_emails, prefix="measurements-concurrent"
    )
    source = create_source(client, token, uuid4().hex)
    source_id = str(source["id"])
    content = FIXTURE.read_bytes()
    preview = preview_workbook(client, token, content)
    decisions = decisions_for(preview)
    plan = plan_workbook(
        client,
        token,
        source_id=source_id,
        content=content,
        preview=preview,
        decisions=decisions,
    )

    def submit() -> tuple[int, str]:
        with TestClient(app) as threaded_client:
            response = confirm_workbook(
                threaded_client,
                token,
                source_id=source_id,
                content=content,
                preview=preview,
                plan=plan,
                decisions=decisions,
                idempotency_key="concurrent-same-key-0005",
            )
            return response.status_code, response.json()["id"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: submit(), range(2)))

    assert sorted(status_code for status_code, _ in results) == [200, 201]
    assert len({import_id for _, import_id in results}) == 1

    changed_content = workbook_with_change("D5", 74.75)
    changed_preview = preview_workbook(client, token, changed_content)
    changed_decisions = decisions_for(changed_preview)
    next_plan = plan_workbook(
        client,
        token,
        source_id=source_id,
        content=changed_content,
        preview=changed_preview,
        decisions=changed_decisions,
    )
    assert next_plan["totals"]["modified"] == 1
    changed_decisions["modifications"] = [
        {"revision_index": 0, "action": "create_version"}
    ]

    def submit_distinct(key: str) -> int:
        with TestClient(app) as threaded_client:
            response = confirm_workbook(
                threaded_client,
                token,
                source_id=source_id,
                content=changed_content,
                preview=changed_preview,
                plan=next_plan,
                decisions=changed_decisions,
                idempotency_key=key,
            )
            return response.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        conflict_results = list(
            executor.map(
                submit_distinct,
                ["parallel-first-key-0006", "parallel-second-key-0007"],
            )
        )

    assert sorted(conflict_results) == [201, 409]
    with get_session_factory()() as session:
        assert (
            session.scalar(
                select(func.count(BodyMeasurementImport.id)).where(
                    BodyMeasurementImport.user_id == user_id
                )
            )
            == 2
        )
        source_row = session.scalar(
            select(BodyMeasurementSource).where(
                BodyMeasurementSource.user_id == user_id
            )
        )
        assert source_row is not None
        assert source_row.history_version == 2
        assert (
            session.scalar(
                select(func.count(BodyMeasurementReview.id)).where(
                    BodyMeasurementReview.user_id == user_id
                )
            )
            == 4
        )
        assert (
            session.scalar(
                select(func.count(BodyMeasurementReview.id)).where(
                    BodyMeasurementReview.user_id == user_id,
                    BodyMeasurementReview.is_current.is_(True),
                )
            )
            == 3
        )
        session.execute(delete(User).where(User.id == user_id))
        session.commit()

    with get_session_factory()() as session:
        assert (
            session.scalar(
                select(func.count(BodyMeasurementSource.id)).where(
                    BodyMeasurementSource.user_id == user_id
                )
            )
            == 0
        )
        assert (
            session.scalar(
                select(func.count(BodyMeasurementImport.id)).where(
                    BodyMeasurementImport.user_id == user_id
                )
            )
            == 0
        )
        assert (
            session.scalar(
                select(func.count(BodyMeasurementReview.id)).where(
                    BodyMeasurementReview.user_id == user_id
                )
            )
            == 0
        )
