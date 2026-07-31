from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MeasurementCategory = Literal[
    "bioimpedance",
    "skinfold",
    "circumference",
]
MeasurementSide = Literal["none", "left", "right"]
MeasurementUnit = Literal[
    "kg",
    "cm",
    "mm",
    "percent",
    "kcal_per_day",
    "years",
    "unitless_index",
    "unitless_level",
]
UnitSource = Literal["excel", "adapter_v1", "unresolved"]
DateStatus = Literal["resolved", "missing_year"]


class PreviewIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    blocking: bool
    revision_label: str | None = None
    metric_code: str | None = None


class TechnicalMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_size_bytes: int = Field(ge=0)
    sheet_count: int = Field(ge=1)
    supported_sheet: str
    used_rows: int = Field(ge=1)
    used_columns: int = Field(ge=1)
    zip_entry_count: int = Field(ge=1)
    uncompressed_size_bytes: int = Field(ge=1)
    content_type_signal: Literal["xlsx", "generic", "missing"]


class MeasurementPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    category: MeasurementCategory
    side: MeasurementSide
    value: str
    unit: MeasurementUnit | None
    unit_source: UnitSource
    original_label: str
    origin: Literal["reported"] = "reported"


class RevisionPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_date: str
    normalized_date: date | None
    label: str
    date_status: DateStatus
    inferred_year: int | None = None
    metrics: list[MeasurementPreview]


class UnknownMetricPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_label: str
    side: MeasurementSide
    original_label: str
    populated_revision_count: int = Field(ge=0)


class IgnoredCellPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference: str
    reason: Literal["empty_metric_value", "separator_row", "unsupported_section"]


class PreviewTotals(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_count: int = Field(ge=0)
    recognized_metric_values: int = Field(ge=0)
    unknown_metric_rows: int = Field(ge=0)
    ignored_cells: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    error_count: int = Field(ge=0)
    has_blocking_errors: bool


class BodyMeasurementImportPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    adapter_version: Literal["body-measurements-v1"]
    fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    metadata: TechnicalMetadata
    revisions: list[RevisionPreview]
    warnings: list[PreviewIssue]
    errors: list[PreviewIssue]
    unknown_metrics: list[UnknownMetricPreview]
    ignored_cells: list[IgnoredCellPreview]
    totals: PreviewTotals
