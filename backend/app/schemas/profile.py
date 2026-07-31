from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID
from zoneinfo import available_timezones

from pydantic import BaseModel, ConfigDict, Field, field_validator

ExperienceLevel = Literal["beginner", "intermediate", "advanced"]
UnitSystem = Literal["metric", "imperial"]
HeightCm = Annotated[
    Decimal,
    Field(
        gt=0,
        le=300,
        max_digits=5,
        decimal_places=2,
        allow_inf_nan=False,
    ),
]

_iana_timezones = frozenset(available_timezones())


class ProfileUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    display_name: str = Field(min_length=1, max_length=80)
    birth_date: date | None = None
    height_cm: HeightCm | None = None
    experience_level: ExperienceLevel
    timezone: str = Field(min_length=1, max_length=64)
    unit_system: UnitSystem

    @field_validator("birth_date")
    @classmethod
    def birth_date_must_not_be_in_the_future(
        cls,
        value: date | None,
    ) -> date | None:
        if value is not None and value > datetime.now(UTC).date():
            raise ValueError("birth_date must not be in the future")
        return value

    @field_validator("height_cm", mode="before")
    @classmethod
    def height_must_not_be_boolean(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("height_cm must be a number")
        return value

    @field_validator("timezone")
    @classmethod
    def timezone_must_be_iana(cls, value: str) -> str:
        if value not in _iana_timezones:
            raise ValueError("timezone must be a valid IANA identifier")
        return value


class ProfilePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    display_name: str
    birth_date: date | None
    height_cm: float | None
    experience_level: ExperienceLevel
    timezone: str
    unit_system: UnitSystem
    created_at: datetime
    updated_at: datetime
