from datetime import UTC, datetime

from fastapi import Response

from app.core.config import Settings, get_settings


def set_refresh_cookie(
    response: Response,
    refresh_token: str,
    expires_at: datetime,
    *,
    settings: Settings | None = None,
    now: datetime | None = None,
) -> None:
    cookie_settings = settings or get_settings()
    current_time = (now or datetime.now(UTC)).astimezone(UTC)
    expires_at_utc = expires_at.astimezone(UTC)
    max_age = max(0, int((expires_at_utc - current_time).total_seconds()))
    response.set_cookie(
        key=cookie_settings.refresh_cookie_name,
        value=refresh_token,
        max_age=max_age,
        expires=expires_at_utc,
        path=cookie_settings.refresh_cookie_path,
        domain=cookie_settings.refresh_cookie_domain,
        secure=cookie_settings.refresh_cookie_secure,
        httponly=True,
        samesite=cookie_settings.refresh_cookie_samesite,
    )


def clear_refresh_cookie(
    response: Response,
    *,
    settings: Settings | None = None,
) -> None:
    cookie_settings = settings or get_settings()
    response.delete_cookie(
        key=cookie_settings.refresh_cookie_name,
        path=cookie_settings.refresh_cookie_path,
        domain=cookie_settings.refresh_cookie_domain,
        secure=cookie_settings.refresh_cookie_secure,
        httponly=True,
        samesite=cookie_settings.refresh_cookie_samesite,
    )
