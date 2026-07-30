import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.csrf import InvalidCsrfOriginError, validate_request_origin


def build_settings() -> Settings:
    return Settings(
        jwt_secret_key=SecretStr("test-only-jwt-secret-with-at-least-32-bytes"),
        cors_allowed_origins=["https://app.example.com"],
        csrf_trusted_origins=["https://app.example.com"],
    )


def test_trusted_origin_is_accepted() -> None:
    validate_request_origin(
        "https://app.example.com/",
        required=True,
        settings=build_settings(),
    )


def test_missing_origin_is_only_allowed_for_compatible_non_browser_login() -> None:
    validate_request_origin(None, required=False, settings=build_settings())

    with pytest.raises(InvalidCsrfOriginError):
        validate_request_origin(
            None,
            required=True,
            settings=build_settings(),
        )


@pytest.mark.parametrize(
    "origin",
    ["https://attacker.example", "null", "", "https://app.example.com.evil"],
)
def test_untrusted_origin_is_rejected(origin: str) -> None:
    with pytest.raises(InvalidCsrfOriginError):
        validate_request_origin(
            origin,
            required=True,
            settings=build_settings(),
        )
