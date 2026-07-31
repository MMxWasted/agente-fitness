from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.body_measurement_history import (
    BodyMeasurementImportDecisions,
    BodyMeasurementSourceCreate,
)
from app.schemas.body_measurement_import import BodyMeasurementImportPreview
from app.services.body_measurement_imports.preparation import (
    InvalidImportDecisionError,
    PreparedMetric,
    canonical_decimal,
    make_content_hash,
    make_request_digest,
    make_revision_identity_key,
    prepare_import,
    validate_persisted_decimal,
)
from app.services.body_measurement_imports.workbook import (
    BodyMeasurementWorkbookAdapterV1,
    WorkbookPolicy,
    validate_xlsx_archive,
)

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "body_measurements"
    / "body_measurements_format_v1.xlsx"
)
XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
POLICY = WorkbookPolicy(
    max_file_size_bytes=5 * 1024 * 1024,
    max_zip_entries=512,
    max_uncompressed_size_bytes=25 * 1024 * 1024,
)


def preview_fixture() -> BodyMeasurementImportPreview:
    content = FIXTURE.read_bytes()
    metadata = validate_xlsx_archive(
        content,
        filename="measurements.xlsx",
        content_type=XLSX_CONTENT_TYPE,
        policy=POLICY,
    )
    return BodyMeasurementWorkbookAdapterV1().preview(
        content,
        archive_metadata=metadata,
    )


def valid_decisions(
    preview: BodyMeasurementImportPreview,
) -> BodyMeasurementImportDecisions:
    return BodyMeasurementImportDecisions.model_validate(
        {
            "date_resolutions": [
                {"revision_index": 1, "measurement_date": "2026-03-06"}
            ],
            "excluded_unknown_metrics": [
                {
                    "category_label": unknown.category_label,
                    "original_label": unknown.original_label,
                    "side": unknown.side,
                }
                for unknown in preview.unknown_metrics
            ],
        }
    )


def test_preparation_requires_explicit_resolutions_and_exclusions() -> None:
    preview = preview_fixture()
    user_id = uuid4()
    source_id = uuid4()

    blocked = prepare_import(
        preview,
        user_id=user_id,
        source_id=source_id,
        decisions=BodyMeasurementImportDecisions(),
        today=date(2026, 7, 31),
    )
    prepared = prepare_import(
        preview,
        user_id=user_id,
        source_id=source_id,
        decisions=valid_decisions(preview),
        today=date(2026, 7, 31),
    )

    assert any("revision_year_required" in item.issues for item in blocked.reviews)
    assert all(
        "unknown_metrics_not_excluded" in item.issues for item in blocked.reviews
    )
    assert all(not item.issues for item in prepared.reviews)
    assert prepared.reviews[1].measurement_date == date(2026, 3, 6)
    assert prepared.confirmed_fingerprint.startswith("sha256:")


def test_preparation_rejects_untrusted_or_stale_decisions() -> None:
    preview = preview_fixture()

    with pytest.raises(ValidationError):
        BodyMeasurementImportDecisions.model_validate({"values": [{"value": 1}]})

    with pytest.raises(InvalidImportDecisionError):
        prepare_import(
            preview,
            user_id=uuid4(),
            source_id=uuid4(),
            decisions=BodyMeasurementImportDecisions.model_validate(
                {"excluded_revisions": [99]}
            ),
        )


def test_source_input_normalizes_display_name_and_logical_key() -> None:
    source = BodyMeasurementSourceCreate.model_validate(
        {
            "display_name": "  Revisión   principal  ",
            "logical_key": "  EXCEL.Principal  ",
        }
    )

    assert source.display_name == "Revisión principal"
    assert source.logical_key == "excel.principal"


def test_request_digest_is_canonical_but_sensitive_to_the_request() -> None:
    source_id = uuid4()
    first = BodyMeasurementImportDecisions.model_validate(
        {
            "excluded_revisions": [2, 0],
            "date_resolutions": [
                {"revision_index": 1, "measurement_date": "2026-03-06"},
                {"revision_index": 3, "measurement_date": "2026-05-08"},
            ],
        }
    )
    reordered = BodyMeasurementImportDecisions.model_validate(
        {
            "excluded_revisions": [0, 2],
            "date_resolutions": list(reversed(first.model_dump()["date_resolutions"])),
        }
    )

    def digest_for(
        decisions: BodyMeasurementImportDecisions,
        *,
        history_version: int = 4,
    ) -> str:
        return make_request_digest(
            source_id=source_id,
            file_sha256="a" * 64,
            preview_fingerprint=f"sha256:{'b' * 64}",
            confirmed_fingerprint=f"sha256:{'c' * 64}",
            history_version=history_version,
            decisions=decisions,
        )

    digest = digest_for(first)

    assert digest == digest_for(reordered)
    assert digest != digest_for(first, history_version=5)


def test_identity_and_content_hashes_have_distinct_stable_inputs() -> None:
    user_id = uuid4()
    source_id = uuid4()
    metric = PreparedMetric(
        code="body_weight",
        category="bioimpedance",
        side="none",
        value=Decimal("72.400"),
        canonical_value="72.4",
        unit="kg",
        original_label="Peso corporal",
        origin="reported",
    )

    identity = make_revision_identity_key(
        user_id=user_id,
        source_id=source_id,
        measurement_date=date(2026, 1, 15),
        normalized_label="2026-01-15",
        disambiguator="",
    )
    same_identity = make_revision_identity_key(
        user_id=user_id,
        source_id=source_id,
        measurement_date=date(2026, 1, 15),
        normalized_label="2026-01-15",
        disambiguator="",
    )
    other_identity = make_revision_identity_key(
        user_id=user_id,
        source_id=source_id,
        measurement_date=date(2026, 1, 15),
        normalized_label="2026-01-15",
        disambiguator="second-review",
    )

    assert identity == same_identity
    assert identity != other_identity
    assert make_content_hash([metric]) == make_content_hash([metric])
    assert identity != make_content_hash([metric])


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("72.400000", "72.4"), ("0.000000", "0"), ("-0.000000", "0")],
)
def test_decimal_values_are_validated_without_silent_rounding(
    raw: str,
    expected: str,
) -> None:
    value, canonical = validate_persisted_decimal(raw)

    assert canonical_decimal(value) == expected
    assert canonical == expected


@pytest.mark.parametrize("raw", ["1.0000001", "123456789", "NaN", "Infinity"])
def test_decimal_values_outside_numeric_contract_are_rejected(raw: str) -> None:
    with pytest.raises(InvalidImportDecisionError):
        validate_persisted_decimal(raw)
