from functools import lru_cache
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_JWT_SECRET = "local-development-only-replace-with-at-least-32-random-bytes"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Agente Fitness API"
    environment: Literal["development", "test", "production"] = "development"
    cors_allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://agente_fitness:change_me_local_only"
        "@localhost:5432/agente_fitness"
    )
    database_connect_timeout_seconds: int = Field(default=3, ge=1, le=30)
    jwt_secret_key: SecretStr = Field()
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr) -> SecretStr:
        try:
            parsed = urlsplit(value.get_secret_value())
            port = parsed.port
        except ValueError as error:
            raise ValueError("DATABASE_URL must be a valid URL") from error

        if (
            parsed.scheme != "postgresql+psycopg"
            or not parsed.username
            or not parsed.password
            or not parsed.hostname
            or port is None
            or not parsed.path.removeprefix("/")
        ):
            raise ValueError(
                "DATABASE_URL must use postgresql+psycopg and include "
                "username, password, host, port, and database"
            )

        return value

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value().encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 bytes")

        return value

    @model_validator(mode="after")
    def reject_development_secret_in_production(self) -> Self:
        if (
            self.environment == "production"
            and self.jwt_secret_key.get_secret_value() == DEVELOPMENT_JWT_SECRET
        ):
            raise ValueError(
                "JWT_SECRET_KEY must be replaced outside local development"
            )

        return self


@lru_cache
def get_settings() -> Settings:
    # BaseSettings supplies this required field from JWT_SECRET_KEY at runtime.
    return Settings()  # type: ignore[call-arg]
