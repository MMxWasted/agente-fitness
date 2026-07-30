from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app

client = TestClient(app)


def test_health_returns_expected_contract_without_database() -> None:
    def unavailable_database() -> None:
        raise RuntimeError("the health endpoint must not access the database")

    app.dependency_overrides[get_db_session] = unavailable_database
    try:
        response = client.get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
