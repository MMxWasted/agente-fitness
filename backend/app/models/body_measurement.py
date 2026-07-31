from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now


class BodyMeasurementSource(Base):
    __tablename__ = "body_measurement_sources"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "logical_key",
            name="uq_body_measurement_sources_user_logical_key",
        ),
        UniqueConstraint(
            "id",
            "user_id",
            name="uq_body_measurement_sources_id_user",
        ),
        CheckConstraint(
            "btrim(display_name) <> ''",
            name="ck_body_measurement_sources_display_name_not_blank",
        ),
        CheckConstraint(
            "source_kind = 'manual_excel'",
            name="ck_body_measurement_sources_source_kind",
        ),
        CheckConstraint(
            "logical_key ~ '^[a-z0-9][a-z0-9._-]{0,63}$'",
            name="ck_body_measurement_sources_logical_key",
        ),
        CheckConstraint(
            "history_version >= 0",
            name="ck_body_measurement_sources_history_version_nonnegative",
        ),
        Index("ix_body_measurement_sources_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_body_measurement_sources_user_id_users",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    source_kind: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="manual_excel",
        server_default="manual_excel",
    )
    logical_key: Mapped[str] = mapped_column(String(64), nullable=False)
    history_version: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        server_default="0",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"BodyMeasurementSource(id={self.id!r}, user_id={self.user_id!r}, "
            f"history_version={self.history_version!r})"
        )


class BodyMeasurementImport(Base):
    __tablename__ = "body_measurement_imports"
    __table_args__ = (
        ForeignKeyConstraint(
            ["source_id", "user_id"],
            ["body_measurement_sources.id", "body_measurement_sources.user_id"],
            name="fk_body_measurement_imports_source_owner",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "user_id",
            "idempotency_key_hash",
            name="uq_body_measurement_imports_user_idempotency_key",
        ),
        UniqueConstraint(
            "id",
            "user_id",
            "source_id",
            name="uq_body_measurement_imports_id_owner_source",
        ),
        CheckConstraint(
            "idempotency_key_hash ~ '^[0-9a-f]{64}$'",
            name="ck_body_measurement_imports_idempotency_key_hash",
        ),
        CheckConstraint(
            "request_digest ~ '^[0-9a-f]{64}$'",
            name="ck_body_measurement_imports_request_digest",
        ),
        CheckConstraint(
            "file_sha256 ~ '^[0-9a-f]{64}$'",
            name="ck_body_measurement_imports_file_sha256",
        ),
        CheckConstraint(
            "preview_fingerprint ~ '^sha256:[0-9a-f]{64}$'",
            name="ck_body_measurement_imports_preview_fingerprint",
        ),
        CheckConstraint(
            "confirmed_fingerprint ~ '^sha256:[0-9a-f]{64}$'",
            name="ck_body_measurement_imports_confirmed_fingerprint",
        ),
        CheckConstraint(
            "status IN ('completed', 'reverted')",
            name="ck_body_measurement_imports_status",
        ),
        CheckConstraint(
            "created_review_count >= 0 AND skipped_review_count >= 0 "
            "AND versioned_review_count >= 0 AND excluded_review_count >= 0",
            name="ck_body_measurement_imports_counts_nonnegative",
        ),
        CheckConstraint(
            "(status = 'completed' AND reverted_at IS NULL) OR "
            "(status = 'reverted' AND reverted_at IS NOT NULL)",
            name="ck_body_measurement_imports_reverted_state",
        ),
        Index(
            "ix_body_measurement_imports_user_imported_at",
            "user_id",
            "imported_at",
        ),
        Index("ix_body_measurement_imports_source_id", "source_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_body_measurement_imports_user_id_users",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    source_id: Mapped[UUID] = mapped_column(nullable=False)
    idempotency_key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    request_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    adapter_version: Mapped[str] = mapped_column(String(64), nullable=False)
    preview_fingerprint: Mapped[str] = mapped_column(String(71), nullable=False)
    confirmed_fingerprint: Mapped[str] = mapped_column(String(71), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="completed",
        server_default="completed",
    )
    created_review_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    skipped_review_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    versioned_review_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    excluded_review_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
    reverted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"BodyMeasurementImport(id={self.id!r}, user_id={self.user_id!r}, "
            f"source_id={self.source_id!r}, status={self.status!r})"
        )


class BodyMeasurementReview(Base):
    __tablename__ = "body_measurement_reviews"
    __table_args__ = (
        ForeignKeyConstraint(
            ["source_id", "user_id"],
            ["body_measurement_sources.id", "body_measurement_sources.user_id"],
            name="fk_body_measurement_reviews_source_owner",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["import_id", "user_id", "source_id"],
            [
                "body_measurement_imports.id",
                "body_measurement_imports.user_id",
                "body_measurement_imports.source_id",
            ],
            name="fk_body_measurement_reviews_import_owner_source",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["supersedes_review_id", "user_id", "source_id", "identity_key"],
            [
                "body_measurement_reviews.id",
                "body_measurement_reviews.user_id",
                "body_measurement_reviews.source_id",
                "body_measurement_reviews.identity_key",
            ],
            name="fk_body_measurement_reviews_supersedes_same_identity",
        ),
        UniqueConstraint(
            "id",
            "user_id",
            "source_id",
            "identity_key",
            name="uq_body_measurement_reviews_id_owner_source_identity",
        ),
        UniqueConstraint(
            "user_id",
            "source_id",
            "identity_key",
            "version",
            name="uq_body_measurement_reviews_identity_version",
        ),
        UniqueConstraint(
            "supersedes_review_id",
            name="uq_body_measurement_reviews_supersedes_review_id",
        ),
        CheckConstraint(
            "version > 0",
            name="ck_body_measurement_reviews_version_positive",
        ),
        CheckConstraint(
            "supersedes_review_id IS NULL OR id <> supersedes_review_id",
            name="ck_body_measurement_reviews_not_self_superseding",
        ),
        CheckConstraint(
            "btrim(normalized_label) <> ''",
            name="ck_body_measurement_reviews_normalized_label_not_blank",
        ),
        CheckConstraint(
            "identity_key ~ '^[0-9a-f]{64}$'",
            name="ck_body_measurement_reviews_identity_key",
        ),
        CheckConstraint(
            "content_hash ~ '^[0-9a-f]{64}$'",
            name="ck_body_measurement_reviews_content_hash",
        ),
        Index(
            "uq_body_measurement_reviews_current_identity",
            "user_id",
            "source_id",
            "identity_key",
            unique=True,
            postgresql_where=text("is_current = true"),
        ),
        Index(
            "ix_body_measurement_reviews_user_measurement_date",
            "user_id",
            "measurement_date",
        ),
        Index("ix_body_measurement_reviews_import_id", "import_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_body_measurement_reviews_user_id_users",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    source_id: Mapped[UUID] = mapped_column(nullable=False)
    import_id: Mapped[UUID] = mapped_column(nullable=False)
    measurement_date: Mapped[date] = mapped_column(Date, nullable=False)
    original_label: Mapped[str] = mapped_column(String(80), nullable=False)
    normalized_label: Mapped[str] = mapped_column(String(80), nullable=False)
    disambiguator: Mapped[str] = mapped_column(
        String(64), nullable=False, default="", server_default=""
    )
    identity_key: Mapped[str] = mapped_column(String(64), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    supersedes_review_id: Mapped[UUID | None] = mapped_column(nullable=True)
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now(),
    )
    values: Mapped[list["BodyMeasurementValue"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by=lambda: (
            BodyMeasurementValue.category,
            BodyMeasurementValue.metric_code,
            BodyMeasurementValue.side,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"BodyMeasurementReview(id={self.id!r}, user_id={self.user_id!r}, "
            f"version={self.version!r}, is_current={self.is_current!r})"
        )


class BodyMeasurementValue(Base):
    __tablename__ = "body_measurement_values"
    __table_args__ = (
        UniqueConstraint(
            "review_id",
            "metric_code",
            "side",
            name="uq_body_measurement_values_review_metric_side",
        ),
        CheckConstraint(
            "category IN ('bioimpedance', 'skinfold', 'circumference')",
            name="ck_body_measurement_values_category",
        ),
        CheckConstraint(
            "side IN ('none', 'left', 'right')",
            name="ck_body_measurement_values_side",
        ),
        CheckConstraint(
            "unit IN ('kg', 'cm', 'mm', 'percent', 'kcal_per_day', "
            "'years', 'unitless_index', 'unitless_level')",
            name="ck_body_measurement_values_unit",
        ),
        CheckConstraint(
            "origin = 'reported'",
            name="ck_body_measurement_values_origin",
        ),
        Index("ix_body_measurement_values_review_id", "review_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    review_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "body_measurement_reviews.id",
            name="fk_body_measurement_values_review_id_reviews",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    metric_code: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    original_label: Mapped[str] = mapped_column(String(80), nullable=False)
    origin: Mapped[str] = mapped_column(
        String(16), nullable=False, default="reported", server_default="reported"
    )
    catalog_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )
    review: Mapped[BodyMeasurementReview] = relationship(back_populates="values")

    def __repr__(self) -> str:
        return (
            f"BodyMeasurementValue(id={self.id!r}, review_id={self.review_id!r}, "
            f"metric_code={self.metric_code!r}, side={self.side!r})"
        )
