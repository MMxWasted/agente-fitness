import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

from app.schemas.body_measurement_history import BodyMeasurementImportDecisions
from app.schemas.body_measurement_import import BodyMeasurementImportPreview
from app.services.body_measurement_imports.catalog import (
    CATALOG_VERSION,
    METRICS_BY_CODE,
    normalize_label,
)

_DATE_WITHOUT_YEAR = re.compile(r"^(?P<day>\d{1,2})[-/](?P<month>\d{1,2})$")


class InvalidImportDecisionError(ValueError):
    """Raised when client decisions do not match the reanalysed workbook."""


@dataclass(frozen=True)
class PreparedMetric:
    code: str
    category: str
    side: str
    value: Decimal
    canonical_value: str
    unit: str
    original_label: str
    origin: str
    catalog_version: str = CATALOG_VERSION


@dataclass
class PreparedReview:
    revision_index: int
    original_label: str
    normalized_label: str
    measurement_date: date | None
    disambiguator: str
    metrics: list[PreparedMetric]
    excluded: bool = False
    issues: list[str] = field(default_factory=list)
    identity_key: str | None = None
    content_hash: str | None = None


@dataclass(frozen=True)
class PreparedImport:
    reviews: list[PreparedReview]
    confirmed_fingerprint: str


def prepare_import(
    preview: BodyMeasurementImportPreview,
    *,
    user_id: UUID,
    source_id: UUID,
    decisions: BodyMeasurementImportDecisions,
    today: date | None = None,
) -> PreparedImport:
    current_date = today or datetime.now(UTC).date()
    revision_count = len(preview.revisions)
    _validate_revision_indexes(decisions, revision_count)

    date_resolutions = {
        decision.revision_index: decision.measurement_date
        for decision in decisions.date_resolutions
    }
    disambiguators = {
        decision.revision_index: normalize_label(decision.disambiguator)[:64]
        for decision in decisions.disambiguators
    }
    if any(not value for value in disambiguators.values()):
        raise InvalidImportDecisionError("A disambiguator becomes empty")

    excluded_revisions = set(decisions.excluded_revisions)
    excluded_metrics = {
        (item.revision_index, item.metric_code, item.side)
        for item in decisions.excluded_metrics
    }
    unit_resolutions = {
        (item.metric_code, item.side): item.action
        for item in decisions.unit_resolutions
    }
    known_metric_selectors = {
        (revision_index, metric.code, metric.side)
        for revision_index, revision in enumerate(preview.revisions)
        for metric in revision.metrics
    }
    issue_revision_indexes = {
        (issue.revision_label, issue.metric_code): revision_index
        for revision_index, revision in enumerate(preview.revisions)
        for issue in preview.errors
        if issue.revision_label == revision.label and issue.metric_code is not None
    }
    for (
        _revision_label,
        metric_code,
    ), revision_index in issue_revision_indexes.items():
        definition = METRICS_BY_CODE.get(metric_code)
        if definition is not None:
            known_metric_selectors.update(
                (revision_index, metric_code, side) for side in definition.allowed_sides
            )
    if not excluded_metrics.issubset(known_metric_selectors):
        raise InvalidImportDecisionError(
            "A metric exclusion does not match the workbook"
        )

    known_unit_selectors = {
        (metric.code, metric.side)
        for revision in preview.revisions
        for metric in revision.metrics
        if metric.unit is None
    }
    if not set(unit_resolutions).issubset(known_unit_selectors):
        raise InvalidImportDecisionError(
            "A unit resolution does not match an ambiguous workbook metric"
        )

    unknown_metrics = {
        (item.category_label, item.original_label, item.side)
        for item in preview.unknown_metrics
    }
    excluded_unknown_metrics = {
        (item.category_label, item.original_label, item.side)
        for item in decisions.excluded_unknown_metrics
    }
    if not excluded_unknown_metrics.issubset(unknown_metrics):
        raise InvalidImportDecisionError(
            "An unknown metric exclusion does not match the workbook"
        )

    global_issues: list[str] = []
    if unknown_metrics != excluded_unknown_metrics:
        global_issues.append("unknown_metrics_not_excluded")

    parser_issues_by_revision: dict[int, list[str]] = {}
    resolvable_parser_codes = {
        "duplicate_revision_date",
        "revision_year_required",
        "unit_mismatch",
    }
    for issue in preview.errors:
        if not issue.blocking or issue.code in resolvable_parser_codes:
            continue
        matching_indexes = [
            index
            for index, revision in enumerate(preview.revisions)
            if revision.label == issue.revision_label
        ]
        if not matching_indexes:
            global_issues.append(f"workbook_error:{issue.code}")
            continue
        for revision_index in matching_indexes:
            definition = (
                METRICS_BY_CODE.get(issue.metric_code)
                if issue.metric_code is not None
                else None
            )
            is_excluded = definition is not None and all(
                (revision_index, definition.code, side) in excluded_metrics
                for side in definition.allowed_sides
            )
            if not is_excluded:
                parser_issues_by_revision.setdefault(revision_index, []).append(
                    f"workbook_error:{issue.code}"
                )

    prepared_reviews: list[PreparedReview] = []
    for revision_index, revision in enumerate(preview.revisions):
        excluded = revision_index in excluded_revisions
        measurement_date = revision.normalized_date
        issues: list[str] = []
        if revision.date_status == "missing_year":
            resolution = date_resolutions.get(revision_index)
            if resolution is None:
                issues.append("revision_year_required")
                measurement_date = None
            else:
                _validate_date_resolution(
                    revision.raw_date,
                    resolution,
                    current_date,
                )
                measurement_date = resolution
        elif revision_index in date_resolutions:
            raise InvalidImportDecisionError(
                "A resolved revision cannot receive another date"
            )

        if measurement_date is not None and measurement_date > current_date:
            raise InvalidImportDecisionError("Future measurement dates are invalid")

        metrics: list[PreparedMetric] = []
        for metric in revision.metrics:
            selector = (revision_index, metric.code, metric.side)
            if selector in excluded_metrics:
                continue
            definition = METRICS_BY_CODE.get(metric.code)
            if definition is None or metric.side not in definition.allowed_sides:
                raise InvalidImportDecisionError(
                    "The workbook contains an unsupported metric identity"
                )
            unit = metric.unit
            if unit is None:
                if unit_resolutions.get((metric.code, metric.side)) != (
                    "accept_canonical"
                ):
                    issues.append(f"unit_resolution_required:{metric.code}")
                    continue
                unit = definition.unit
            elif unit != definition.unit:
                raise InvalidImportDecisionError(
                    "The workbook metric unit is not canonical"
                )

            value, canonical_value = validate_persisted_decimal(metric.value)
            metrics.append(
                PreparedMetric(
                    code=metric.code,
                    category=metric.category,
                    side=metric.side,
                    value=value,
                    canonical_value=canonical_value,
                    unit=unit,
                    original_label=metric.original_label[:80],
                    origin=metric.origin,
                )
            )

        if not metrics and not excluded:
            issues.append("revision_has_no_measurements")
        issues.extend(parser_issues_by_revision.get(revision_index, []))
        issues.extend(global_issues)
        if excluded:
            issues = []

        normalized_label = (
            measurement_date.isoformat() if measurement_date is not None else "pending"
        )
        disambiguator = disambiguators.get(revision_index, "")
        prepared = PreparedReview(
            revision_index=revision_index,
            original_label=revision.raw_date[:80],
            normalized_label=normalized_label,
            measurement_date=measurement_date,
            disambiguator=disambiguator,
            metrics=sorted(
                metrics,
                key=lambda item: (item.category, item.code, item.side),
            ),
            excluded=excluded,
            issues=sorted(set(issues)),
        )
        if measurement_date is not None:
            prepared.identity_key = make_revision_identity_key(
                user_id=user_id,
                source_id=source_id,
                measurement_date=measurement_date,
                normalized_label=normalized_label,
                disambiguator=disambiguator,
            )
            prepared.content_hash = make_content_hash(prepared.metrics)
        prepared_reviews.append(prepared)

    _mark_duplicate_identities(prepared_reviews)
    _validate_all_decisions_were_used(
        preview,
        decisions,
        prepared_reviews,
    )
    return PreparedImport(
        reviews=prepared_reviews,
        confirmed_fingerprint=make_confirmed_fingerprint(prepared_reviews),
    )


def validate_persisted_decimal(value: str) -> tuple[Decimal, str]:
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as error:
        raise InvalidImportDecisionError("A measurement is not decimal") from error
    if not decimal_value.is_finite():
        raise InvalidImportDecisionError("A measurement must be finite")
    exponent = decimal_value.as_tuple().exponent
    scale = max(-int(exponent), 0)
    integer_digits = max(len(decimal_value.as_tuple().digits) - scale, 0)
    if scale > 6 or integer_digits > 8:
        raise InvalidImportDecisionError(
            "A measurement exceeds NUMERIC(14,6) precision"
        )
    return decimal_value, canonical_decimal(decimal_value)


def canonical_decimal(value: Decimal) -> str:
    normalized = format(value.normalize(), "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return "0" if normalized in {"-0", ""} else normalized


def make_revision_identity_key(
    *,
    user_id: UUID,
    source_id: UUID,
    measurement_date: date,
    normalized_label: str,
    disambiguator: str,
) -> str:
    return _sha256_json(
        {
            "user_id": str(user_id),
            "source_id": str(source_id),
            "measurement_date": measurement_date.isoformat(),
            "normalized_label": normalize_label(normalized_label),
            "disambiguator": normalize_label(disambiguator),
        }
    )


def make_content_hash(metrics: list[PreparedMetric]) -> str:
    return _sha256_json(
        [
            {
                "code": metric.code,
                "category": metric.category,
                "side": metric.side,
                "value": metric.canonical_value,
                "unit": metric.unit,
                "origin": metric.origin,
                "catalog_version": metric.catalog_version,
            }
            for metric in sorted(
                metrics,
                key=lambda item: (item.category, item.code, item.side),
            )
        ]
    )


def make_confirmed_fingerprint(reviews: list[PreparedReview]) -> str:
    digest = _sha256_json(
        [
            {
                "revision_index": review.revision_index,
                "excluded": review.excluded,
                "measurement_date": (
                    review.measurement_date.isoformat()
                    if review.measurement_date is not None
                    else None
                ),
                "normalized_label": review.normalized_label,
                "disambiguator": review.disambiguator,
                "identity_key": review.identity_key,
                "content_hash": review.content_hash,
                "issues": review.issues,
            }
            for review in reviews
        ]
    )
    return f"sha256:{digest}"


def canonical_decisions(
    decisions: BodyMeasurementImportDecisions,
    *,
    include_modifications: bool,
) -> dict[str, object]:
    payload = decisions.model_dump(mode="json")
    if not include_modifications:
        payload.pop("modifications", None)
    for key, value in payload.items():
        if isinstance(value, list):
            payload[key] = sorted(
                value,
                key=lambda item: json.dumps(
                    item,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
            )
    return payload


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def make_request_digest(
    *,
    source_id: UUID,
    file_sha256: str,
    preview_fingerprint: str,
    confirmed_fingerprint: str,
    history_version: int,
    decisions: BodyMeasurementImportDecisions,
) -> str:
    return _sha256_json(
        {
            "source_id": str(source_id),
            "file_sha256": file_sha256,
            "preview_fingerprint": preview_fingerprint,
            "confirmed_fingerprint": confirmed_fingerprint,
            "history_version": history_version,
            "decisions": canonical_decisions(
                decisions,
                include_modifications=True,
            ),
        }
    )


def _sha256_json(value: object) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_revision_indexes(
    decisions: BodyMeasurementImportDecisions,
    revision_count: int,
) -> None:
    indexes = set(decisions.excluded_revisions)
    indexes.update(item.revision_index for item in decisions.date_resolutions)
    indexes.update(item.revision_index for item in decisions.excluded_metrics)
    indexes.update(item.revision_index for item in decisions.disambiguators)
    indexes.update(item.revision_index for item in decisions.modifications)
    if any(index >= revision_count for index in indexes):
        raise InvalidImportDecisionError(
            "A revision decision does not match the workbook"
        )


def _validate_date_resolution(
    raw_date: str,
    resolution: date,
    today: date,
) -> None:
    match = _DATE_WITHOUT_YEAR.fullmatch(raw_date.strip())
    if match is None:
        raise InvalidImportDecisionError(
            "A date resolution does not match an ambiguous date"
        )
    if (
        int(match.group("day")) != resolution.day
        or int(match.group("month")) != resolution.month
        or resolution > today
    ):
        raise InvalidImportDecisionError(
            "A date resolution changes the original day or month"
        )


def _mark_duplicate_identities(reviews: list[PreparedReview]) -> None:
    by_identity: dict[str, list[PreparedReview]] = {}
    for review in reviews:
        if review.excluded or review.identity_key is None:
            continue
        by_identity.setdefault(review.identity_key, []).append(review)
    for duplicates in by_identity.values():
        if len(duplicates) > 1:
            for review in duplicates:
                review.issues.append("duplicate_revision_identity")
                review.issues.sort()


def _validate_all_decisions_were_used(
    preview: BodyMeasurementImportPreview,
    decisions: BodyMeasurementImportDecisions,
    prepared_reviews: list[PreparedReview],
) -> None:
    missing_date_indexes = {
        index
        for index, revision in enumerate(preview.revisions)
        if revision.date_status == "missing_year"
    }
    if not {item.revision_index for item in decisions.date_resolutions}.issubset(
        missing_date_indexes
    ):
        raise InvalidImportDecisionError("A date resolution is not required")

    excluded = set(decisions.excluded_revisions)
    for disambiguation in decisions.disambiguators:
        if disambiguation.revision_index in excluded:
            raise InvalidImportDecisionError(
                "An excluded revision cannot be disambiguated"
            )
    for modification in decisions.modifications:
        if modification.revision_index in excluded:
            raise InvalidImportDecisionError(
                "An excluded revision cannot receive a modification action"
            )
    if len(prepared_reviews) != len(preview.revisions):
        raise InvalidImportDecisionError("The prepared workbook is incomplete")
