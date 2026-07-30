import os

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "unit-test-only-secret-that-is-at-least-32-bytes",
)
