import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal

from app.schemas.body_measurement_import import (
    MeasurementCategory,
    MeasurementSide,
    MeasurementUnit,
)

CATALOG_VERSION = "body-measurements-v1"

_WHITESPACE_PATTERN = re.compile(r"\s+")
_PUNCTUATION_PATTERN = re.compile(r"[^a-z0-9%]+")


@dataclass(frozen=True)
class MetricDefinition:
    code: str
    category: MeasurementCategory
    aliases: tuple[str, ...]
    unit: MeasurementUnit
    allowed_sides: tuple[MeasurementSide, ...]
    minimum: Decimal
    maximum: Decimal
    origin: str = "reported"


def normalize_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    without_marks = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return _WHITESPACE_PATTERN.sub(
        " ",
        _PUNCTUATION_PATTERN.sub(" ", without_marks),
    ).strip()


def limited_label(value: object, *, maximum: int = 80) -> str:
    if not isinstance(value, str):
        return str(value)[:maximum]
    return _WHITESPACE_PATTERN.sub(" ", value.strip())[:maximum]


def split_laterality(label: str) -> tuple[str, MeasurementSide]:
    normalized = normalize_label(label)
    tokens = normalized.split()
    side: MeasurementSide = "none"
    side_aliases: dict[str, MeasurementSide] = {
        "izquierdo": "left",
        "izquierda": "left",
        "izq": "left",
        "left": "left",
        "derecho": "right",
        "derecha": "right",
        "der": "right",
        "right": "right",
    }
    remaining: list[str] = []
    for token in tokens:
        detected_side = side_aliases.get(token)
        if detected_side is None:
            remaining.append(token)
            continue
        if side != "none" and side != detected_side:
            return " ".join(remaining), "none"
        side = detected_side
    return " ".join(remaining), side


def _metric(
    code: str,
    category: MeasurementCategory,
    aliases: tuple[str, ...],
    unit: MeasurementUnit,
    *,
    bilateral: bool = False,
    minimum: str = "0",
    maximum: str = "10000",
) -> MetricDefinition:
    allowed_sides: tuple[MeasurementSide, ...] = (
        ("left", "right") if bilateral else ("none",)
    )
    return MetricDefinition(
        code=code,
        category=category,
        aliases=tuple(normalize_label(alias) for alias in aliases),
        unit=unit,
        allowed_sides=allowed_sides,
        minimum=Decimal(minimum),
        maximum=Decimal(maximum),
    )


METRIC_CATALOG: tuple[MetricDefinition, ...] = (
    _metric(
        "body_weight",
        "bioimpedance",
        ("peso corporal", "peso"),
        "kg",
        maximum="500",
    ),
    _metric(
        "body_mass_index_reported",
        "bioimpedance",
        ("índice de masa corporal", "imc", "bmi"),
        "unitless_index",
        maximum="150",
    ),
    _metric(
        "body_fat_percentage",
        "bioimpedance",
        ("grasa corporal", "porcentaje de grasa"),
        "percent",
        maximum="100",
    ),
    _metric(
        "body_water_percentage",
        "bioimpedance",
        ("agua corporal", "porcentaje de agua"),
        "percent",
        maximum="100",
    ),
    _metric(
        "muscle_mass",
        "bioimpedance",
        ("masa muscular",),
        "kg",
        maximum="500",
    ),
    _metric(
        "physique_rating",
        "bioimpedance",
        ("valoración física", "valoracion fisica", "physique rating"),
        "unitless_level",
        maximum="20",
    ),
    _metric(
        "bone_mass",
        "bioimpedance",
        ("masa ósea", "masa osea"),
        "kg",
        maximum="30",
    ),
    _metric(
        "basal_metabolic_rate",
        "bioimpedance",
        ("metabolismo basal", "tasa metabólica basal", "bmr"),
        "kcal_per_day",
        maximum="10000",
    ),
    _metric(
        "metabolic_age",
        "bioimpedance",
        ("edad metabólica", "edad metabolica"),
        "years",
        maximum="150",
    ),
    _metric(
        "visceral_fat_level",
        "bioimpedance",
        ("grasa visceral", "nivel de grasa visceral"),
        "unitless_level",
        maximum="100",
    ),
    _metric(
        "quadriceps_skinfold",
        "skinfold",
        ("cuádriceps", "cuadriceps"),
        "mm",
        bilateral=True,
        maximum="150",
    ),
    _metric(
        "triceps_skinfold",
        "skinfold",
        ("tríceps", "triceps"),
        "mm",
        bilateral=True,
        maximum="150",
    ),
    _metric(
        "subscapular_skinfold",
        "skinfold",
        ("subescapular", "pliegue subescapular"),
        "mm",
        maximum="150",
    ),
    _metric(
        "side_skinfold",
        "skinfold",
        ("costado", "lateral"),
        "mm",
        bilateral=True,
        maximum="150",
    ),
    _metric(
        "abdominal_skinfold",
        "skinfold",
        ("abdominal", "abdomen"),
        "mm",
        maximum="150",
    ),
    _metric(
        "waist_circumference",
        "circumference",
        ("cintura", "perímetro de cintura"),
        "cm",
        maximum="400",
    ),
    _metric(
        "hip_circumference",
        "circumference",
        ("cadera", "perímetro de cadera"),
        "cm",
        maximum="400",
    ),
    _metric(
        "shoulder_circumference",
        "circumference",
        ("hombros", "perímetro de hombros"),
        "cm",
        maximum="400",
    ),
    _metric(
        "chest_back_circumference",
        "circumference",
        ("pecho y espalda", "pecho espalda", "tórax"),
        "cm",
        maximum="400",
    ),
    _metric(
        "thigh_circumference",
        "circumference",
        ("muslo",),
        "cm",
        bilateral=True,
        maximum="250",
    ),
    _metric(
        "arm_circumference",
        "circumference",
        ("brazo",),
        "cm",
        bilateral=True,
        maximum="150",
    ),
    _metric(
        "flexed_arm_circumference",
        "circumference",
        ("brazo flexionado", "brazo contraído", "brazo contraido"),
        "cm",
        bilateral=True,
        maximum="150",
    ),
)

METRICS_BY_ALIAS = {
    alias: metric for metric in METRIC_CATALOG for alias in metric.aliases
}
METRICS_BY_CODE = {metric.code: metric for metric in METRIC_CATALOG}

CATEGORY_ALIASES: dict[str, MeasurementCategory] = {
    "bioimpedancia": "bioimpedance",
    "plicometro": "skinfold",
    "pliegues": "skinfold",
    "perimetros": "circumference",
}

UNIT_ALIASES: dict[str, MeasurementUnit] = {
    "kg": "kg",
    "kilogramo": "kg",
    "kilogramos": "kg",
    "cm": "cm",
    "mm": "mm",
    "%": "percent",
    "porcentaje": "percent",
    "kcal dia": "kcal_per_day",
    "kcal por dia": "kcal_per_day",
    "anos": "years",
    "ano": "years",
    "indice": "unitless_index",
    "nivel": "unitless_level",
}
