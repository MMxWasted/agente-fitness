import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings


def test_database_url_is_postgresql_and_masked() -> None:
    password = "not-a-real-secret"
    settings = Settings(
        database_url=SecretStr(
            "postgresql+psycopg://agente_fitness:"
            f"{password}@localhost:5432/agente_fitness"
        )
    )

    assert settings.database_url.get_secret_value().startswith("postgresql+psycopg://")
    assert password not in repr(settings)
    assert settings.cors_allowed_origins == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    assert settings.database_connect_timeout_seconds == 3


def test_database_url_rejects_non_postgresql_driver() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url=SecretStr("sqlite:///local.db"))
