from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.body_measurement import (
    BodyMeasurementImport,
    BodyMeasurementReview,
    BodyMeasurementSource,
    BodyMeasurementValue,
)
from app.models.user import User
from app.repositories.body_measurement import (
    add_body_measurement_import,
    add_body_measurement_review,
    add_body_measurement_source,
    get_body_measurement_import,
    get_body_measurement_review,
    get_body_measurement_source,
    get_body_measurement_source_for_update,
    get_current_reviews_by_identity,
    get_import_by_idempotency_key_hash,
    get_review_successors,
    get_reviews_by_ids_for_update,
    list_body_measurement_imports,
    list_body_measurement_reviews,
    list_body_measurement_sources,
    list_reviews_created_by_import,
)
from app.schemas.body_measurement_history import (
    BodyMeasurementImportDecisions,
    BodyMeasurementImportList,
    BodyMeasurementImportPlan,
    BodyMeasurementImportPublic,
    BodyMeasurementReviewDetail,
    BodyMeasurementReviewList,
    BodyMeasurementReviewPublic,
    BodyMeasurementSourceCreate,
    BodyMeasurementSourceList,
    BodyMeasurementSourcePublic,
    BodyMeasurementValuePublic,
    ImportPlanItem,
    ImportPlanTotals,
)
from app.services.body_measurement_imports.preparation import (
    PreparedImport,
    PreparedReview,
    canonical_decimal,
    make_request_digest,
    prepare_import,
    sha256_bytes,
    sha256_text,
)


class BodyMeasurementHistoryError(ValueError):
    """Base error for safe body-measurement history failures."""


class BodyMeasurementResourceNotFoundError(BodyMeasurementHistoryError):
    """Raised when an owned private resource is not visible."""


class BodyMeasurementConflictError(BodyMeasurementHistoryError):
    """Raised when optimistic, idempotency, or version state conflicts."""


class BodyMeasurementValidationError(BodyMeasurementHistoryError):
    """Raised when a confirmed plan contains blocking or invalid decisions."""


@dataclass(frozen=True)
class ConfirmationResult:
    measurement_import: BodyMeasurementImportPublic
    replayed: bool


def create_source(
    session: Session,
    user: User,
    source_data: BodyMeasurementSourceCreate,
) -> BodyMeasurementSourcePublic:
    source = BodyMeasurementSource(
        user_id=user.id,
        display_name=source_data.display_name,
        source_kind=source_data.source_kind,
        logical_key=source_data.logical_key,
    )
    add_body_measurement_source(session, source)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise BodyMeasurementConflictError(
            "Source logical key already exists"
        ) from error
    session.refresh(source)
    return BodyMeasurementSourcePublic.model_validate(source)


def read_sources(
    session: Session,
    user: User,
    *,
    limit: int,
    offset: int,
) -> BodyMeasurementSourceList:
    items, total = list_body_measurement_sources(
        session,
        user.id,
        limit=limit,
        offset=offset,
    )
    return BodyMeasurementSourceList(
        items=[BodyMeasurementSourcePublic.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


def plan_import(
    session: Session,
    user: User,
    *,
    source_id: UUID,
    preview: object,
    decisions: BodyMeasurementImportDecisions,
) -> BodyMeasurementImportPlan:
    from app.schemas.body_measurement_import import BodyMeasurementImportPreview

    if not isinstance(preview, BodyMeasurementImportPreview):
        raise TypeError("preview must be a BodyMeasurementImportPreview")
    source = get_body_measurement_source(session, user.id, source_id)
    if source is None:
        raise BodyMeasurementResourceNotFoundError("Source not found")
    prepared = prepare_import(
        preview,
        user_id=user.id,
        source_id=source.id,
        decisions=decisions,
    )
    current = get_current_reviews_by_identity(
        session,
        user.id,
        source.id,
        _identity_keys(prepared),
    )
    return _build_plan(source, prepared, current)


def confirm_import(
    session: Session,
    user: User,
    *,
    source_id: UUID,
    content: bytes,
    preview: object,
    preview_fingerprint: str,
    confirmed_fingerprint: str,
    history_version: int,
    decisions: BodyMeasurementImportDecisions,
    idempotency_key: str,
) -> ConfirmationResult:
    from app.schemas.body_measurement_import import BodyMeasurementImportPreview

    if not isinstance(preview, BodyMeasurementImportPreview):
        raise TypeError("preview must be a BodyMeasurementImportPreview")
    if preview.fingerprint != preview_fingerprint:
        raise BodyMeasurementConflictError("Workbook preview changed")

    prepared = prepare_import(
        preview,
        user_id=user.id,
        source_id=source_id,
        decisions=decisions,
    )
    if prepared.confirmed_fingerprint != confirmed_fingerprint:
        raise BodyMeasurementConflictError("Confirmed workbook plan changed")

    file_hash = sha256_bytes(content)
    idempotency_key_hash = sha256_text(idempotency_key)
    request_digest = make_request_digest(
        source_id=source_id,
        file_sha256=file_hash,
        preview_fingerprint=preview_fingerprint,
        confirmed_fingerprint=confirmed_fingerprint,
        history_version=history_version,
        decisions=decisions,
    )

    source = get_body_measurement_source_for_update(session, user.id, source_id)
    if source is None:
        session.rollback()
        raise BodyMeasurementResourceNotFoundError("Source not found")

    previous_import = get_import_by_idempotency_key_hash(
        session,
        user.id,
        idempotency_key_hash,
    )
    if previous_import is not None:
        if previous_import.request_digest != request_digest:
            session.rollback()
            raise BodyMeasurementConflictError("Idempotency key was reused")
        result = _import_public(previous_import)
        session.rollback()
        return ConfirmationResult(measurement_import=result, replayed=True)

    if source.history_version != history_version:
        session.rollback()
        raise BodyMeasurementConflictError("Measurement history changed")

    if any(review.issues for review in prepared.reviews if not review.excluded):
        session.rollback()
        raise BodyMeasurementValidationError("The import plan is blocked")

    current = get_current_reviews_by_identity(
        session,
        user.id,
        source.id,
        _identity_keys(prepared),
        for_update=True,
    )
    classifications = _classify(prepared, current)
    modification_actions = {
        item.revision_index: item.action for item in decisions.modifications
    }
    modified_indexes = {
        review.revision_index
        for review, classification, _ in classifications
        if classification == "modified"
    }
    if not set(modification_actions).issubset(modified_indexes):
        session.rollback()
        raise BodyMeasurementValidationError(
            "A modification decision does not match a modified revision"
        )
    if any(
        modification_actions.get(index, "reject") != "create_version"
        for index in modified_indexes
    ):
        session.rollback()
        raise BodyMeasurementConflictError(
            "A modified revision requires explicit versioning"
        )

    counts = _classification_counts(classifications)
    now = datetime.now(UTC)
    measurement_import = BodyMeasurementImport(
        user_id=user.id,
        source_id=source.id,
        idempotency_key_hash=idempotency_key_hash,
        request_digest=request_digest,
        file_sha256=file_hash,
        adapter_version=preview.adapter_version,
        preview_fingerprint=preview_fingerprint,
        confirmed_fingerprint=confirmed_fingerprint,
        status="completed",
        created_review_count=counts["new"],
        skipped_review_count=counts["identical"],
        versioned_review_count=counts["modified"],
        excluded_review_count=counts["excluded"],
        imported_at=now,
        created_at=now,
        updated_at=now,
    )
    add_body_measurement_import(session, measurement_import)
    try:
        session.flush()
        for _prepared_review, classification, existing in classifications:
            if classification == "modified" and existing is not None:
                existing.is_current = False
                existing.updated_at = now
        session.flush()

        for prepared_review, classification, existing in classifications:
            if classification not in {"new", "modified"}:
                continue
            review = _new_review(
                prepared_review,
                measurement_import=measurement_import,
                user_id=user.id,
                source_id=source.id,
                previous=existing,
                now=now,
            )
            add_body_measurement_review(session, review)

        source.history_version += 1
        source.updated_at = now
        session.commit()
    except Exception:
        session.rollback()
        raise

    session.refresh(measurement_import)
    return ConfirmationResult(
        measurement_import=_import_public(measurement_import),
        replayed=False,
    )


def read_imports(
    session: Session,
    user: User,
    *,
    source_id: UUID | None,
    status: str | None,
    imported_from: datetime | None,
    imported_to: datetime | None,
    limit: int,
    offset: int,
) -> BodyMeasurementImportList:
    if imported_from is not None and imported_to is not None:
        if imported_from > imported_to:
            raise BodyMeasurementValidationError("Invalid import date range")
    items, total = list_body_measurement_imports(
        session,
        user.id,
        source_id=source_id,
        status=status,
        imported_from=imported_from,
        imported_to=imported_to,
        limit=limit,
        offset=offset,
    )
    return BodyMeasurementImportList(
        items=[_import_public(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


def read_import(
    session: Session,
    user: User,
    import_id: UUID,
) -> BodyMeasurementImportPublic:
    measurement_import = get_body_measurement_import(session, user.id, import_id)
    if measurement_import is None:
        raise BodyMeasurementResourceNotFoundError("Import not found")
    return _import_public(measurement_import)


def read_reviews(
    session: Session,
    user: User,
    *,
    source_id: UUID | None,
    measured_from: date | None,
    measured_to: date | None,
    current: bool | None,
    limit: int,
    offset: int,
) -> BodyMeasurementReviewList:
    if measured_from is not None and measured_to is not None:
        if measured_from > measured_to:
            raise BodyMeasurementValidationError("Invalid measurement date range")
    items, total = list_body_measurement_reviews(
        session,
        user.id,
        source_id=source_id,
        measured_from=measured_from,
        measured_to=measured_to,
        current=current,
        limit=limit,
        offset=offset,
    )
    return BodyMeasurementReviewList(
        items=[_review_public(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


def read_review(
    session: Session,
    user: User,
    review_id: UUID,
) -> BodyMeasurementReviewDetail:
    review = get_body_measurement_review(session, user.id, review_id)
    if review is None:
        raise BodyMeasurementResourceNotFoundError("Review not found")
    summary = _review_public(review)
    return BodyMeasurementReviewDetail(
        **summary.model_dump(),
        values=[
            BodyMeasurementValuePublic(
                id=value.id,
                metric_code=value.metric_code,
                category=value.category,  # type: ignore[arg-type]
                side=value.side,  # type: ignore[arg-type]
                value=canonical_decimal(value.value),
                unit=value.unit,  # type: ignore[arg-type]
                original_label=value.original_label,
                origin="reported",
                catalog_version=value.catalog_version,
            )
            for value in review.values
        ],
    )


def revert_import(
    session: Session,
    user: User,
    import_id: UUID,
) -> bool:
    initial_import = get_body_measurement_import(session, user.id, import_id)
    if initial_import is None:
        raise BodyMeasurementResourceNotFoundError("Import not found")
    source = get_body_measurement_source_for_update(
        session,
        user.id,
        initial_import.source_id,
    )
    if source is None:
        session.rollback()
        raise BodyMeasurementResourceNotFoundError("Import not found")
    measurement_import = get_body_measurement_import(
        session,
        user.id,
        import_id,
        for_update=True,
    )
    if measurement_import is None:
        session.rollback()
        raise BodyMeasurementResourceNotFoundError("Import not found")
    if measurement_import.status == "reverted":
        session.rollback()
        return False

    reviews = list_reviews_created_by_import(
        session,
        user.id,
        import_id,
        for_update=True,
    )
    review_ids = {review.id for review in reviews}
    successors = get_review_successors(session, review_ids)
    if any(successor.import_id != import_id for successor in successors):
        session.rollback()
        raise BodyMeasurementConflictError(
            "A later review version depends on this import"
        )

    predecessor_ids = {
        review.supersedes_review_id
        for review in reviews
        if review.supersedes_review_id is not None
        and review.supersedes_review_id not in review_ids
    }
    predecessors = get_reviews_by_ids_for_update(
        session,
        user.id,
        predecessor_ids,
    )
    now = datetime.now(UTC)
    try:
        for review in reviews:
            review.is_current = False
        session.flush()
        for review in reviews:
            session.delete(review)
        session.flush()
        for predecessor in predecessors.values():
            predecessor.is_current = True
            predecessor.updated_at = now
        measurement_import.status = "reverted"
        measurement_import.reverted_at = now
        measurement_import.updated_at = now
        source.history_version += 1
        source.updated_at = now
        session.commit()
    except Exception:
        session.rollback()
        raise
    return True


def _identity_keys(prepared: PreparedImport) -> set[str]:
    return {
        review.identity_key
        for review in prepared.reviews
        if not review.excluded and review.identity_key is not None
    }


def _classify(
    prepared: PreparedImport,
    current: dict[str, BodyMeasurementReview],
) -> list[tuple[PreparedReview, str, BodyMeasurementReview | None]]:
    result: list[tuple[PreparedReview, str, BodyMeasurementReview | None]] = []
    for review in prepared.reviews:
        if review.excluded:
            result.append((review, "excluded", None))
            continue
        if review.issues or review.identity_key is None or review.content_hash is None:
            result.append((review, "blocked", None))
            continue
        existing = current.get(review.identity_key)
        if existing is None:
            result.append((review, "new", None))
        elif existing.content_hash == review.content_hash:
            result.append((review, "identical", existing))
        else:
            result.append((review, "modified", existing))
    return result


def _build_plan(
    source: BodyMeasurementSource,
    prepared: PreparedImport,
    current: dict[str, BodyMeasurementReview],
) -> BodyMeasurementImportPlan:
    classifications = _classify(prepared, current)
    counts = _classification_counts(classifications)
    return BodyMeasurementImportPlan(
        source_id=source.id,
        history_version=source.history_version,
        confirmed_fingerprint=prepared.confirmed_fingerprint,
        revisions=[
            ImportPlanItem(
                revision_index=review.revision_index,
                label=review.original_label,
                measurement_date=review.measurement_date,
                disambiguator=review.disambiguator,
                classification=classification,  # type: ignore[arg-type]
                metric_count=len(review.metrics),
                current_review_id=existing.id if existing is not None else None,
                current_version=existing.version if existing is not None else None,
                issues=review.issues,
            )
            for review, classification, existing in classifications
        ],
        totals=ImportPlanTotals(**counts),
    )


def _classification_counts(
    classifications: list[tuple[PreparedReview, str, BodyMeasurementReview | None]],
) -> dict[str, int]:
    counts = {
        "new": 0,
        "identical": 0,
        "modified": 0,
        "blocked": 0,
        "excluded": 0,
    }
    for _, classification, _ in classifications:
        counts[classification] += 1
    return counts


def _new_review(
    prepared: PreparedReview,
    *,
    measurement_import: BodyMeasurementImport,
    user_id: UUID,
    source_id: UUID,
    previous: BodyMeasurementReview | None,
    now: datetime,
) -> BodyMeasurementReview:
    if (
        prepared.measurement_date is None
        or prepared.identity_key is None
        or prepared.content_hash is None
    ):
        raise BodyMeasurementValidationError("A persisted revision must be complete")
    review = BodyMeasurementReview(
        user_id=user_id,
        source_id=source_id,
        import_id=measurement_import.id,
        measurement_date=prepared.measurement_date,
        original_label=prepared.original_label,
        normalized_label=prepared.normalized_label,
        disambiguator=prepared.disambiguator,
        identity_key=prepared.identity_key,
        content_hash=prepared.content_hash,
        version=1 if previous is None else previous.version + 1,
        supersedes_review_id=None if previous is None else previous.id,
        is_current=True,
        created_at=now,
        updated_at=now,
    )
    review.values = [
        BodyMeasurementValue(
            metric_code=metric.code,
            category=metric.category,
            side=metric.side,
            value=metric.value,
            unit=metric.unit,
            original_label=metric.original_label,
            origin=metric.origin,
            catalog_version=metric.catalog_version,
            created_at=now,
        )
        for metric in prepared.metrics
    ]
    return review


def _import_public(
    measurement_import: BodyMeasurementImport,
) -> BodyMeasurementImportPublic:
    persisted_or_skipped = (
        measurement_import.created_review_count
        + measurement_import.skipped_review_count
        + measurement_import.versioned_review_count
    )
    if measurement_import.excluded_review_count > 0 and persisted_or_skipped == 0:
        outcome = "excluded"
    elif measurement_import.excluded_review_count > 0:
        outcome = "partial"
    elif (
        sum(
            count > 0
            for count in (
                measurement_import.created_review_count,
                measurement_import.skipped_review_count,
                measurement_import.versioned_review_count,
            )
        )
        > 1
    ):
        outcome = "mixed"
    elif measurement_import.versioned_review_count > 0:
        outcome = "versioned"
    elif measurement_import.created_review_count > 0:
        outcome = "created"
    else:
        outcome = "skipped"
    return BodyMeasurementImportPublic(
        id=measurement_import.id,
        source_id=measurement_import.source_id,
        status=measurement_import.status,  # type: ignore[arg-type]
        adapter_version=measurement_import.adapter_version,
        outcome=outcome,  # type: ignore[arg-type]
        created_review_count=measurement_import.created_review_count,
        skipped_review_count=measurement_import.skipped_review_count,
        versioned_review_count=measurement_import.versioned_review_count,
        excluded_review_count=measurement_import.excluded_review_count,
        imported_at=measurement_import.imported_at,
        reverted_at=measurement_import.reverted_at,
    )


def _review_public(review: BodyMeasurementReview) -> BodyMeasurementReviewPublic:
    return BodyMeasurementReviewPublic(
        id=review.id,
        source_id=review.source_id,
        import_id=review.import_id,
        measurement_date=review.measurement_date,
        original_label=review.original_label,
        normalized_label=review.normalized_label,
        disambiguator=review.disambiguator,
        version=review.version,
        supersedes_review_id=review.supersedes_review_id,
        is_current=review.is_current,
        metric_count=len(review.values),
        created_at=review.created_at,
    )
