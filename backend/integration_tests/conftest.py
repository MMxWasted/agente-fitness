import os
from collections.abc import Generator
from urllib.parse import urlsplit

import pytest

from app.core.config import get_settings

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "integration-test-only-secret-that-is-at-least-32-bytes",
)


@pytest.fixture(scope="session", autouse=True)
def require_dedicated_test_database() -> Generator[None]:
    database_url = get_settings().database_url.get_secret_value()
    database_name = urlsplit(database_url).path.removeprefix("/")
    if not database_name.endswith(("_test", "_ci")):
        raise pytest.UsageError(
            "Integration tests require a dedicated PostgreSQL database whose "
            "name ends in _test or _ci."
        )

    yield
