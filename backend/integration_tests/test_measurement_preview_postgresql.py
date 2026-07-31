import pytest
from sqlalchemy import inspect

from app.db.session import get_engine

pytestmark = pytest.mark.integration


def test_measurement_preview_adds_no_persistence_tables() -> None:
    assert set(inspect(get_engine()).get_table_names()) == {
        "alembic_version",
        "auth_sessions",
        "user_profiles",
        "users",
    }
