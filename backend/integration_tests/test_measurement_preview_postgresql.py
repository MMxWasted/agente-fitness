import pytest
from sqlalchemy import inspect

from app.db.session import get_engine

pytestmark = pytest.mark.integration


def test_body_measurement_history_tables_are_migrated() -> None:
    assert set(inspect(get_engine()).get_table_names()) == {
        "alembic_version",
        "auth_sessions",
        "body_measurement_imports",
        "body_measurement_reviews",
        "body_measurement_sources",
        "body_measurement_values",
        "user_profiles",
        "users",
    }
