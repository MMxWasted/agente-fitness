from datetime import UTC, datetime, timedelta

from fastapi import Response
from pydantic import SecretStr

from app.core.config import Settings
from app.core.cookies import clear_refresh_cookie, set_refresh_cookie


def build_settings(*, secure: bool = False) -> Settings:
    return Settings(
        jwt_secret_key=SecretStr("test-only-jwt-secret-with-at-least-32-bytes"),
        refresh_cookie_secure=secure,
    )


def test_refresh_cookie_has_required_security_attributes() -> None:
    response = Response()
    now = datetime(2026, 7, 30, 12, tzinfo=UTC)

    set_refresh_cookie(
        response,
        "opaque-test-value",
        now + timedelta(days=7),
        settings=build_settings(secure=True),
        now=now,
    )

    header = response.headers["set-cookie"]
    assert "agente_fitness_refresh=" in header
    assert "HttpOnly" in header
    assert "Secure" in header
    assert "SameSite=lax" in header
    assert "Path=/api/v1/auth" in header
    assert "Max-Age=604800" in header


def test_cookie_deletion_uses_the_same_scope() -> None:
    response = Response()

    clear_refresh_cookie(response, settings=build_settings())

    header = response.headers["set-cookie"]
    assert "agente_fitness_refresh=" in header
    assert "Max-Age=0" in header
    assert "HttpOnly" in header
    assert "SameSite=lax" in header
    assert "Path=/api/v1/auth" in header
