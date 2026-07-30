import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import DEVELOPMENT_JWT_SECRET, Settings

TEST_JWT_SECRET = SecretStr("test-only-jwt-secret-with-at-least-32-bytes")


def test_database_url_is_postgresql_and_masked() -> None:
    password = "not-a-real-secret"
    settings = Settings(
        database_url=SecretStr(
            "postgresql+psycopg://agente_fitness:"
            f"{password}@localhost:5432/agente_fitness"
        ),
        jwt_secret_key=TEST_JWT_SECRET,
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
        Settings(
            database_url=SecretStr("sqlite:///local.db"),
            jwt_secret_key=TEST_JWT_SECRET,
        )


def test_jwt_configuration_is_validated_and_masked() -> None:
    secret = "test-only-jwt-secret-with-at-least-32-bytes"
    settings = Settings(jwt_secret_key=SecretStr(secret))

    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30
    assert secret not in repr(settings)


def test_jwt_secret_rejects_short_values() -> None:
    with pytest.raises(ValidationError):
        Settings(jwt_secret_key=SecretStr("too-short"))


def test_production_rejects_the_documented_development_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            jwt_secret_key=SecretStr(DEVELOPMENT_JWT_SECRET),
        )
