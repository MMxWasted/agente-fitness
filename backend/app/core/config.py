from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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


@lru_cache
def get_settings() -> Settings:
    return Settings()
