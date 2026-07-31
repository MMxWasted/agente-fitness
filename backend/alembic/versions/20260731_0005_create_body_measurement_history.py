"""Create private versioned body measurement history.

Revision ID: 20260731_0005
Revises: 20260730_0004
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260731_0005"
down_revision: str | Sequence[str] | None = "20260730_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "body_measurement_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column(
            "source_kind",
            sa.String(length=32),
            server_default="manual_excel",
            nullable=False,
        ),
        sa.Column("logical_key", sa.String(length=64), nullable=False),
        sa.Column(
            "history_version", sa.BigInteger(), server_default="0", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "btrim(display_name) <> ''",
            name="ck_body_measurement_sources_display_name_not_blank",
        ),
        sa.CheckConstraint(
            "source_kind = 'manual_excel'",
            name="ck_body_measurement_sources_source_kind",
        ),
        sa.CheckConstraint(
            "logical_key ~ '^[a-z0-9][a-z0-9._-]{0,63}$'",
            name="ck_body_measurement_sources_logical_key",
        ),
        sa.CheckConstraint(
            "history_version >= 0",
            name="ck_body_measurement_sources_history_version_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_body_measurement_sources_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_body_measurement_sources"),
        sa.UniqueConstraint(
            "user_id",
            "logical_key",
            name="uq_body_measurement_sources_user_logical_key",
        ),
        sa.UniqueConstraint(
            "id", "user_id", name="uq_body_measurement_sources_id_user"
        ),
    )
    op.create_index(
        "ix_body_measurement_sources_user_id",
        "body_measurement_sources",
        ["user_id"],
    )

    op.create_table(
        "body_measurement_imports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key_hash", sa.String(length=64), nullable=False),
        sa.Column("request_digest", sa.String(length=64), nullable=False),
        sa.Column("file_sha256", sa.String(length=64), nullable=False),
        sa.Column("adapter_version", sa.String(length=64), nullable=False),
        sa.Column("preview_fingerprint", sa.String(length=71), nullable=False),
        sa.Column("confirmed_fingerprint", sa.String(length=71), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default="completed",
            nullable=False,
        ),
        sa.Column(
            "created_review_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "skipped_review_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "versioned_review_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "excluded_review_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "imported_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("reverted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "idempotency_key_hash ~ '^[0-9a-f]{64}$'",
            name="ck_body_measurement_imports_idempotency_key_hash",
        ),
        sa.CheckConstraint(
            "request_digest ~ '^[0-9a-f]{64}$'",
            name="ck_body_measurement_imports_request_digest",
        ),
        sa.CheckConstraint(
            "file_sha256 ~ '^[0-9a-f]{64}$'",
            name="ck_body_measurement_imports_file_sha256",
        ),
        sa.CheckConstraint(
            "preview_fingerprint ~ '^sha256:[0-9a-f]{64}$'",
            name="ck_body_measurement_imports_preview_fingerprint",
        ),
        sa.CheckConstraint(
            "confirmed_fingerprint ~ '^sha256:[0-9a-f]{64}$'",
            name="ck_body_measurement_imports_confirmed_fingerprint",
        ),
        sa.CheckConstraint(
            "status IN ('completed', 'reverted')",
            name="ck_body_measurement_imports_status",
        ),
        sa.CheckConstraint(
            "created_review_count >= 0 AND skipped_review_count >= 0 "
            "AND versioned_review_count >= 0 AND excluded_review_count >= 0",
            name="ck_body_measurement_imports_counts_nonnegative",
        ),
        sa.CheckConstraint(
            "(status = 'completed' AND reverted_at IS NULL) OR "
            "(status = 'reverted' AND reverted_at IS NOT NULL)",
            name="ck_body_measurement_imports_reverted_state",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_body_measurement_imports_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_id", "user_id"],
            ["body_measurement_sources.id", "body_measurement_sources.user_id"],
            name="fk_body_measurement_imports_source_owner",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_body_measurement_imports"),
        sa.UniqueConstraint(
            "user_id",
            "idempotency_key_hash",
            name="uq_body_measurement_imports_user_idempotency_key",
        ),
        sa.UniqueConstraint(
            "id",
            "user_id",
            "source_id",
            name="uq_body_measurement_imports_id_owner_source",
        ),
    )
    op.create_index(
        "ix_body_measurement_imports_user_imported_at",
        "body_measurement_imports",
        ["user_id", "imported_at"],
    )
    op.create_index(
        "ix_body_measurement_imports_source_id",
        "body_measurement_imports",
        ["source_id"],
    )

    op.create_table(
        "body_measurement_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("import_id", sa.Uuid(), nullable=False),
        sa.Column("measurement_date", sa.Date(), nullable=False),
        sa.Column("original_label", sa.String(length=80), nullable=False),
        sa.Column("normalized_label", sa.String(length=80), nullable=False),
        sa.Column(
            "disambiguator",
            sa.String(length=64),
            server_default="",
            nullable=False,
        ),
        sa.Column("identity_key", sa.String(length=64), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("supersedes_review_id", sa.Uuid(), nullable=True),
        sa.Column("is_current", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "version > 0", name="ck_body_measurement_reviews_version_positive"
        ),
        sa.CheckConstraint(
            "supersedes_review_id IS NULL OR id <> supersedes_review_id",
            name="ck_body_measurement_reviews_not_self_superseding",
        ),
        sa.CheckConstraint(
            "btrim(normalized_label) <> ''",
            name="ck_body_measurement_reviews_normalized_label_not_blank",
        ),
        sa.CheckConstraint(
            "identity_key ~ '^[0-9a-f]{64}$'",
            name="ck_body_measurement_reviews_identity_key",
        ),
        sa.CheckConstraint(
            "content_hash ~ '^[0-9a-f]{64}$'",
            name="ck_body_measurement_reviews_content_hash",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_body_measurement_reviews_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_id", "user_id"],
            ["body_measurement_sources.id", "body_measurement_sources.user_id"],
            name="fk_body_measurement_reviews_source_owner",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["import_id", "user_id", "source_id"],
            [
                "body_measurement_imports.id",
                "body_measurement_imports.user_id",
                "body_measurement_imports.source_id",
            ],
            name="fk_body_measurement_reviews_import_owner_source",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_review_id", "user_id", "source_id", "identity_key"],
            [
                "body_measurement_reviews.id",
                "body_measurement_reviews.user_id",
                "body_measurement_reviews.source_id",
                "body_measurement_reviews.identity_key",
            ],
            name="fk_body_measurement_reviews_supersedes_same_identity",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_body_measurement_reviews"),
        sa.UniqueConstraint(
            "id",
            "user_id",
            "source_id",
            "identity_key",
            name="uq_body_measurement_reviews_id_owner_source_identity",
        ),
        sa.UniqueConstraint(
            "user_id",
            "source_id",
            "identity_key",
            "version",
            name="uq_body_measurement_reviews_identity_version",
        ),
        sa.UniqueConstraint(
            "supersedes_review_id",
            name="uq_body_measurement_reviews_supersedes_review_id",
        ),
    )
    op.create_index(
        "uq_body_measurement_reviews_current_identity",
        "body_measurement_reviews",
        ["user_id", "source_id", "identity_key"],
        unique=True,
        postgresql_where=sa.text("is_current = true"),
    )
    op.create_index(
        "ix_body_measurement_reviews_user_measurement_date",
        "body_measurement_reviews",
        ["user_id", "measurement_date"],
    )
    op.create_index(
        "ix_body_measurement_reviews_import_id",
        "body_measurement_reviews",
        ["import_id"],
    )

    op.create_table(
        "body_measurement_values",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("review_id", sa.Uuid(), nullable=False),
        sa.Column("metric_code", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("value", sa.Numeric(precision=14, scale=6), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("original_label", sa.String(length=80), nullable=False),
        sa.Column(
            "origin",
            sa.String(length=16),
            server_default="reported",
            nullable=False,
        ),
        sa.Column("catalog_version", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "category IN ('bioimpedance', 'skinfold', 'circumference')",
            name="ck_body_measurement_values_category",
        ),
        sa.CheckConstraint(
            "side IN ('none', 'left', 'right')",
            name="ck_body_measurement_values_side",
        ),
        sa.CheckConstraint(
            "unit IN ('kg', 'cm', 'mm', 'percent', 'kcal_per_day', "
            "'years', 'unitless_index', 'unitless_level')",
            name="ck_body_measurement_values_unit",
        ),
        sa.CheckConstraint(
            "origin = 'reported'", name="ck_body_measurement_values_origin"
        ),
        sa.ForeignKeyConstraint(
            ["review_id"],
            ["body_measurement_reviews.id"],
            name="fk_body_measurement_values_review_id_reviews",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_body_measurement_values"),
        sa.UniqueConstraint(
            "review_id",
            "metric_code",
            "side",
            name="uq_body_measurement_values_review_metric_side",
        ),
    )
    op.create_index(
        "ix_body_measurement_values_review_id",
        "body_measurement_values",
        ["review_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_body_measurement_values_review_id",
        table_name="body_measurement_values",
    )
    op.drop_table("body_measurement_values")
    op.drop_index(
        "ix_body_measurement_reviews_import_id",
        table_name="body_measurement_reviews",
    )
    op.drop_index(
        "ix_body_measurement_reviews_user_measurement_date",
        table_name="body_measurement_reviews",
    )
    op.drop_index(
        "uq_body_measurement_reviews_current_identity",
        table_name="body_measurement_reviews",
    )
    op.drop_table("body_measurement_reviews")
    op.drop_index(
        "ix_body_measurement_imports_source_id",
        table_name="body_measurement_imports",
    )
    op.drop_index(
        "ix_body_measurement_imports_user_imported_at",
        table_name="body_measurement_imports",
    )
    op.drop_table("body_measurement_imports")
    op.drop_index(
        "ix_body_measurement_sources_user_id",
        table_name="body_measurement_sources",
    )
    op.drop_table("body_measurement_sources")
