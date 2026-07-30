from app.core.config import Settings, get_settings


class InvalidCsrfOriginError(ValueError):
    """Raised when a browser origin does not satisfy the CSRF policy."""


def validate_request_origin(
    origin: str | None,
    *,
    required: bool,
    settings: Settings | None = None,
) -> None:
    origin_settings = settings or get_settings()
    if origin is None:
        if required:
            raise InvalidCsrfOriginError
        return

    normalized_origin = origin.strip().rstrip("/")
    if normalized_origin not in origin_settings.csrf_trusted_origins:
        raise InvalidCsrfOriginError
