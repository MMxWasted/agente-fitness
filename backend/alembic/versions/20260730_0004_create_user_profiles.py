"""Create private user fitness profiles.

Revision ID: 20260730_0004
Revises: 20260730_0003
Create Date: 2026-07-30
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260730_0004"
down_revision: str | Sequence[str] | None = "20260730_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column(
            "height_cm",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
        ),
        sa.Column(
            "experience_level",
            sa.String(length=16),
            nullable=False,
        ),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("unit_system", sa.String(length=8), nullable=False),
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
            name="ck_user_profiles_display_name_not_blank",
        ),
        sa.CheckConstraint(
            "height_cm > 0 AND height_cm <= 300",
            name="ck_user_profiles_height_cm_range",
        ),
        sa.CheckConstraint(
            "experience_level IN ('beginner', 'intermediate', 'advanced')",
            name="ck_user_profiles_experience_level",
        ),
        sa.CheckConstraint(
            "unit_system IN ('metric', 'imperial')",
            name="ck_user_profiles_unit_system",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_profiles_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_profiles"),
        sa.UniqueConstraint(
            "user_id",
            name="uq_user_profiles_user_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("user_profiles")
