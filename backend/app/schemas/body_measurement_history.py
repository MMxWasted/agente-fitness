from datetime import date, datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.body_measurement_import import (
    MeasurementCategory,
    MeasurementSide,
    MeasurementUnit,
)

ImportStatus = Literal["completed", "reverted"]
ImportOutcome = Literal[
    "created",
    "skipped",
    "versioned",
    "mixed",
    "partial",
    "excluded",
]
PlanClassification = Literal["new", "identical", "modified", "blocked", "excluded"]


class BodyMeasurementSourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=80)
    logical_key: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9][a-z0-9._-]{0,63}$",
    )
    source_kind: Literal["manual_excel"] = "manual_excel"

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("display_name must not be blank")
        return normalized

    @field_validator("logical_key", mode="before")
    @classmethod
    def normalize_logical_key(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class BodyMeasurementSourcePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    display_name: str
    source_kind: Literal["manual_excel"]
    logical_key: str
    history_version: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime


class BodyMeasurementSourceList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[BodyMeasurementSourcePublic]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class RevisionDateResolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_index: int = Field(ge=0)
    measurement_date: date


class MetricSelector(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_index: int = Field(ge=0)
    metric_code: str = Field(min_length=1, max_length=64)
    side: MeasurementSide


class UnitResolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_code: str = Field(min_length=1, max_length=64)
    side: MeasurementSide
    action: Literal["accept_canonical"]


class RevisionDisambiguation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_index: int = Field(ge=0)
    disambiguator: str = Field(min_length=1, max_length=64)


class UnknownMetricExclusion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_label: str = Field(min_length=1, max_length=40)
    original_label: str = Field(min_length=1, max_length=80)
    side: MeasurementSide


class ModificationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_index: int = Field(ge=0)
    action: Literal["reject", "create_version"] = "reject"


class BodyMeasurementImportDecisions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date_resolutions: list[RevisionDateResolution] = Field(default_factory=list)
    unit_resolutions: list[UnitResolution] = Field(default_factory=list)
    excluded_revisions: list[int] = Field(default_factory=list)
    excluded_metrics: list[MetricSelector] = Field(default_factory=list)
    excluded_unknown_metrics: list[UnknownMetricExclusion] = Field(default_factory=list)
    disambiguators: list[RevisionDisambiguation] = Field(default_factory=list)
    modifications: list[ModificationDecision] = Field(default_factory=list)

    @field_validator("excluded_revisions")
    @classmethod
    def validate_excluded_revisions(cls, values: list[int]) -> list[int]:
        if any(value < 0 for value in values):
            raise ValueError("revision indexes must be non-negative")
        if len(values) != len(set(values)):
            raise ValueError("excluded revision indexes must be unique")
        return values

    @model_validator(mode="after")
    def reject_duplicate_decisions(self) -> Self:
        groups: tuple[tuple[str, list[object], object], ...] = (
            (
                "date resolutions",
                list(self.date_resolutions),
                lambda item: item.revision_index,
            ),
            (
                "unit resolutions",
                list(self.unit_resolutions),
                lambda item: (item.metric_code, item.side),
            ),
            (
                "metric exclusions",
                list(self.excluded_metrics),
                lambda item: (item.revision_index, item.metric_code, item.side),
            ),
            (
                "unknown metric exclusions",
                list(self.excluded_unknown_metrics),
                lambda item: (item.category_label, item.original_label, item.side),
            ),
            (
                "disambiguators",
                list(self.disambiguators),
                lambda item: item.revision_index,
            ),
            (
                "modification decisions",
                list(self.modifications),
                lambda item: item.revision_index,
            ),
        )
        for label, items, key_function in groups:
            keys = [key_function(item) for item in items]  # type: ignore[operator]
            if len(keys) != len(set(keys)):
                raise ValueError(f"{label} must not contain duplicates")
        return self


class ImportPlanItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_index: int = Field(ge=0)
    label: str
    measurement_date: date | None
    disambiguator: str
    classification: PlanClassification
    metric_count: int = Field(ge=0)
    current_review_id: UUID | None = None
    current_version: int | None = Field(default=None, ge=1)
    issues: list[str] = Field(default_factory=list)


class ImportPlanTotals(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new: int = Field(ge=0)
    identical: int = Field(ge=0)
    modified: int = Field(ge=0)
    blocked: int = Field(ge=0)
    excluded: int = Field(ge=0)


class BodyMeasurementImportPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: UUID
    history_version: int = Field(ge=0)
    confirmed_fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    revisions: list[ImportPlanItem]
    totals: ImportPlanTotals


class BodyMeasurementImportPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    source_id: UUID
    status: ImportStatus
    adapter_version: str
    outcome: ImportOutcome
    created_review_count: int = Field(ge=0)
    skipped_review_count: int = Field(ge=0)
    versioned_review_count: int = Field(ge=0)
    excluded_review_count: int = Field(ge=0)
    imported_at: datetime
    reverted_at: datetime | None


class BodyMeasurementImportList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[BodyMeasurementImportPublic]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class BodyMeasurementValuePublic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    metric_code: str
    category: MeasurementCategory
    side: MeasurementSide
    value: str
    unit: MeasurementUnit
    original_label: str
    origin: Literal["reported"]
    catalog_version: str


class BodyMeasurementReviewPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    source_id: UUID
    import_id: UUID
    measurement_date: date
    original_label: str
    normalized_label: str
    disambiguator: str
    version: int = Field(ge=1)
    supersedes_review_id: UUID | None
    is_current: bool
    metric_count: int = Field(ge=0)
    created_at: datetime


class BodyMeasurementReviewDetail(BodyMeasurementReviewPublic):
    values: list[BodyMeasurementValuePublic]


class BodyMeasurementReviewList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[BodyMeasurementReviewPublic]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
