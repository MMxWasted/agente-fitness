from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now


class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_profiles_user_id"),
        CheckConstraint(
            "btrim(display_name) <> ''",
            name="ck_user_profiles_display_name_not_blank",
        ),
        CheckConstraint(
            "height_cm > 0 AND height_cm <= 300",
            name="ck_user_profiles_height_cm_range",
        ),
        CheckConstraint(
            "experience_level IN ('beginner', 'intermediate', 'advanced')",
            name="ck_user_profiles_experience_level",
        ),
        CheckConstraint(
            "unit_system IN ('metric', 'imperial')",
            name="ck_user_profiles_unit_system",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_user_profiles_user_id_users",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    height_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    experience_level: Mapped[str] = mapped_column(String(16), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    unit_system: Mapped[str] = mapped_column(String(8), nullable=False)
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
    user: Mapped["User"] = relationship(back_populates="profile")

    def __repr__(self) -> str:
        return f"UserProfile(id={self.id!r}, user_id={self.user_id!r})"


from app.models.user import User  # noqa: E402
