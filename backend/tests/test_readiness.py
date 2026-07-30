from collections.abc import Callable, Generator
from typing import cast
from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.main import app

client = TestClient(app)


def build_session_override(
    session: Session,
) -> Callable[[], Generator[Session]]:
    def override_session() -> Generator[Session]:
        yield session

    return override_session


def test_readiness_returns_ready_when_database_responds() -> None:
    session_mock = Mock(spec=Session)
    session_mock.scalar.return_value = 1
    session = cast(Session, session_mock)
    app.dependency_overrides[get_db_session] = build_session_override(session)

    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    statement = session_mock.scalar.call_args.args[0]
    assert str(statement) == "SELECT 1"


def test_readiness_returns_controlled_error_when_database_fails() -> None:
    session_mock = Mock(spec=Session)
    session_mock.scalar.side_effect = SQLAlchemyError("database unavailable")
    session = cast(Session, session_mock)
    app.dependency_overrides[get_db_session] = build_session_override(session)

    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "database unavailable" not in response.text
