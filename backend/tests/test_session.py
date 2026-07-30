import pytest
from sqlalchemy.orm import Session

from app.db import session as session_module


class TrackingSession(Session):
    was_closed: bool = False

    def close(self) -> None:
        self.was_closed = True
        super().close()


def test_database_dependency_closes_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = TrackingSession()

    def factory() -> TrackingSession:
        return session

    monkeypatch.setattr(session_module, "get_session_factory", lambda: factory)

    dependency = session_module.get_db_session()
    assert next(dependency) is session

    dependency.close()

    assert session.was_closed
