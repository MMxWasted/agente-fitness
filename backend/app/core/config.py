import re
from functools import lru_cache
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_JWT_SECRET = "local-development-only-replace-with-at-least-32-random-bytes"
_COOKIE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9!#$%&'*+\-.^_`|~]+$")
_COOKIE_DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}$)"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$"
)
_COOKIE_PATH_PATTERN = re.compile(r"^/[A-Za-z0-9/_-]*$")


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
    body_measurement_upload_max_bytes: int = Field(
        default=5 * 1024 * 1024,
        ge=1024,
        le=25 * 1024 * 1024,
    )
    body_measurement_zip_max_entries: int = Field(
        default=512,
        ge=16,
        le=4096,
    )
    body_measurement_zip_max_uncompressed_bytes: int = Field(
        default=25 * 1024 * 1024,
        ge=1024,
        le=100 * 1024 * 1024,
    )
    jwt_secret_key: SecretStr = Field()
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=90)
    refresh_cookie_name: str = "agente_fitness_refresh"
    refresh_cookie_secure: bool = False
    refresh_cookie_samesite: Literal["lax", "strict"] = "lax"
    refresh_cookie_domain: str | None = None
    refresh_cookie_path: str = "/api/v1/auth"
    csrf_trusted_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("cors_allowed_origins", "csrf_trusted_origins")
    @classmethod
    def validate_origins(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            origin = value.strip().rstrip("/")
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path
                or parsed.query
                or parsed.fragment
                or "*" in origin
            ):
                raise ValueError(
                    "Origins must be explicit HTTP or HTTPS origins without "
                    "credentials, paths, queries, fragments, or wildcards"
                )
            if origin in normalized:
                raise ValueError("Origins must not contain duplicates")
            normalized.append(origin)

        if not normalized:
            raise ValueError("At least one explicit origin is required")
        return normalized

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

    @field_validator("refresh_cookie_name")
    @classmethod
    def validate_refresh_cookie_name(cls, value: str) -> str:
        name = value.strip()
        if (
            not name
            or _COOKIE_NAME_PATTERN.fullmatch(name) is None
            or name.startswith(("__Host-", "__Secure-"))
        ):
            raise ValueError(
                "REFRESH_COOKIE_NAME must be a valid unprefixed cookie name"
            )
        return name

    @field_validator("refresh_cookie_domain", mode="before")
    @classmethod
    def validate_refresh_cookie_domain(cls, value: object) -> str | None:
        if value is None:
            return None
        domain = str(value).strip()
        if not domain:
            return None
        if _COOKIE_DOMAIN_PATTERN.fullmatch(domain) is None:
            raise ValueError(
                "REFRESH_COOKIE_DOMAIN must be a valid ASCII hostname "
                "without scheme, port, path, or whitespace"
            )
        return domain.lower()

    @field_validator("refresh_cookie_path")
    @classmethod
    def validate_refresh_cookie_path(cls, value: str) -> str:
        path = value.strip()
        if _COOKIE_PATH_PATTERN.fullmatch(path) is None:
            raise ValueError("REFRESH_COOKIE_PATH must be an absolute ASCII API path")
        return path

    @model_validator(mode="after")
    def validate_environment_security(self) -> Self:
        if not set(self.csrf_trusted_origins).issubset(self.cors_allowed_origins):
            raise ValueError(
                "CSRF_TRUSTED_ORIGINS must be included in CORS_ALLOWED_ORIGINS"
            )

        if (
            self.environment == "production"
            and self.jwt_secret_key.get_secret_value() == DEVELOPMENT_JWT_SECRET
        ):
            raise ValueError(
                "JWT_SECRET_KEY must be replaced outside local development"
            )

        if self.environment == "production":
            if not self.refresh_cookie_secure:
                raise ValueError("REFRESH_COOKIE_SECURE must be true in production")
            if any(
                not origin.startswith("https://")
                for origin in (
                    *self.cors_allowed_origins,
                    *self.csrf_trusted_origins,
                )
            ):
                raise ValueError("Production CORS and CSRF origins must use HTTPS")

        return self


@lru_cache
def get_settings() -> Settings:
    # BaseSettings supplies this required field from JWT_SECRET_KEY at runtime.
    return Settings()  # type: ignore[call-arg]
