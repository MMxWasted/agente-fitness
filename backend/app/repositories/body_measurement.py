from datetime import date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.body_measurement import (
    BodyMeasurementImport,
    BodyMeasurementReview,
    BodyMeasurementSource,
)


def add_body_measurement_source(
    session: Session,
    source: BodyMeasurementSource,
) -> None:
    session.add(source)


def get_body_measurement_source(
    session: Session,
    user_id: UUID,
    source_id: UUID,
) -> BodyMeasurementSource | None:
    return session.scalar(
        select(BodyMeasurementSource).where(
            BodyMeasurementSource.id == source_id,
            BodyMeasurementSource.user_id == user_id,
        )
    )


def get_body_measurement_source_for_update(
    session: Session,
    user_id: UUID,
    source_id: UUID,
) -> BodyMeasurementSource | None:
    return session.scalar(
        select(BodyMeasurementSource)
        .where(
            BodyMeasurementSource.id == source_id,
            BodyMeasurementSource.user_id == user_id,
        )
        .with_for_update()
    )


def list_body_measurement_sources(
    session: Session,
    user_id: UUID,
    *,
    limit: int,
    offset: int,
) -> tuple[list[BodyMeasurementSource], int]:
    filters = (BodyMeasurementSource.user_id == user_id,)
    total = session.scalar(
        select(func.count()).select_from(BodyMeasurementSource).where(*filters)
    )
    items = list(
        session.scalars(
            select(BodyMeasurementSource)
            .where(*filters)
            .order_by(
                BodyMeasurementSource.display_name,
                BodyMeasurementSource.id,
            )
            .limit(limit)
            .offset(offset)
        )
    )
    return items, int(total or 0)


def add_body_measurement_import(
    session: Session,
    measurement_import: BodyMeasurementImport,
) -> None:
    session.add(measurement_import)


def get_import_by_idempotency_key_hash(
    session: Session,
    user_id: UUID,
    idempotency_key_hash: str,
) -> BodyMeasurementImport | None:
    return session.scalar(
        select(BodyMeasurementImport).where(
            BodyMeasurementImport.user_id == user_id,
            BodyMeasurementImport.idempotency_key_hash == idempotency_key_hash,
        )
    )


def get_body_measurement_import(
    session: Session,
    user_id: UUID,
    import_id: UUID,
    *,
    for_update: bool = False,
) -> BodyMeasurementImport | None:
    statement = select(BodyMeasurementImport).where(
        BodyMeasurementImport.id == import_id,
        BodyMeasurementImport.user_id == user_id,
    )
    if for_update:
        statement = statement.with_for_update()
    return session.scalar(statement)


def list_body_measurement_imports(
    session: Session,
    user_id: UUID,
    *,
    source_id: UUID | None,
    status: str | None,
    imported_from: datetime | None,
    imported_to: datetime | None,
    limit: int,
    offset: int,
) -> tuple[list[BodyMeasurementImport], int]:
    filters = [BodyMeasurementImport.user_id == user_id]
    if source_id is not None:
        filters.append(BodyMeasurementImport.source_id == source_id)
    if status is not None:
        filters.append(BodyMeasurementImport.status == status)
    if imported_from is not None:
        filters.append(BodyMeasurementImport.imported_at >= imported_from)
    if imported_to is not None:
        filters.append(BodyMeasurementImport.imported_at <= imported_to)

    total = session.scalar(
        select(func.count()).select_from(BodyMeasurementImport).where(*filters)
    )
    items = list(
        session.scalars(
            select(BodyMeasurementImport)
            .where(*filters)
            .order_by(
                BodyMeasurementImport.imported_at.desc(),
                BodyMeasurementImport.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
    )
    return items, int(total or 0)


def add_body_measurement_review(
    session: Session,
    review: BodyMeasurementReview,
) -> None:
    session.add(review)


def get_current_reviews_by_identity(
    session: Session,
    user_id: UUID,
    source_id: UUID,
    identity_keys: set[str],
    *,
    for_update: bool = False,
) -> dict[str, BodyMeasurementReview]:
    if not identity_keys:
        return {}
    statement = select(BodyMeasurementReview).where(
        BodyMeasurementReview.user_id == user_id,
        BodyMeasurementReview.source_id == source_id,
        BodyMeasurementReview.identity_key.in_(identity_keys),
        BodyMeasurementReview.is_current.is_(True),
    )
    if for_update:
        statement = statement.with_for_update()
    return {review.identity_key: review for review in session.scalars(statement)}


def get_body_measurement_review(
    session: Session,
    user_id: UUID,
    review_id: UUID,
) -> BodyMeasurementReview | None:
    return session.scalar(
        select(BodyMeasurementReview)
        .options(selectinload(BodyMeasurementReview.values))
        .where(
            BodyMeasurementReview.id == review_id,
            BodyMeasurementReview.user_id == user_id,
        )
    )


def list_body_measurement_reviews(
    session: Session,
    user_id: UUID,
    *,
    source_id: UUID | None,
    measured_from: date | None,
    measured_to: date | None,
    current: bool | None,
    limit: int,
    offset: int,
) -> tuple[list[BodyMeasurementReview], int]:
    filters = [BodyMeasurementReview.user_id == user_id]
    if source_id is not None:
        filters.append(BodyMeasurementReview.source_id == source_id)
    if measured_from is not None:
        filters.append(BodyMeasurementReview.measurement_date >= measured_from)
    if measured_to is not None:
        filters.append(BodyMeasurementReview.measurement_date <= measured_to)
    if current is not None:
        filters.append(BodyMeasurementReview.is_current.is_(current))

    total = session.scalar(
        select(func.count()).select_from(BodyMeasurementReview).where(*filters)
    )
    items = list(
        session.scalars(
            select(BodyMeasurementReview)
            .options(selectinload(BodyMeasurementReview.values))
            .where(*filters)
            .order_by(
                BodyMeasurementReview.measurement_date.desc(),
                BodyMeasurementReview.normalized_label,
                BodyMeasurementReview.version.desc(),
                BodyMeasurementReview.id,
            )
            .limit(limit)
            .offset(offset)
        )
    )
    return items, int(total or 0)


def list_reviews_created_by_import(
    session: Session,
    user_id: UUID,
    import_id: UUID,
    *,
    for_update: bool = False,
) -> list[BodyMeasurementReview]:
    statement = select(BodyMeasurementReview).where(
        BodyMeasurementReview.user_id == user_id,
        BodyMeasurementReview.import_id == import_id,
    )
    if for_update:
        statement = statement.with_for_update()
    return list(session.scalars(statement))


def get_review_successors(
    session: Session,
    review_ids: set[UUID],
) -> list[BodyMeasurementReview]:
    if not review_ids:
        return []
    return list(
        session.scalars(
            select(BodyMeasurementReview).where(
                BodyMeasurementReview.supersedes_review_id.in_(review_ids)
            )
        )
    )


def get_reviews_by_ids_for_update(
    session: Session,
    user_id: UUID,
    review_ids: set[UUID],
) -> dict[UUID, BodyMeasurementReview]:
    if not review_ids:
        return {}
    return {
        review.id: review
        for review in session.scalars(
            select(BodyMeasurementReview)
            .where(
                BodyMeasurementReview.user_id == user_id,
                BodyMeasurementReview.id.in_(review_ids),
            )
            .with_for_update()
        )
    }
