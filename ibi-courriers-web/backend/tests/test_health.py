"""Tests endpoint health public."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from app.database import Base, engine, get_db
from app.main import app


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    db.close()


def test_health_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" not in data


def test_health_degraded_retourne_503(client):
    with patch("app.health.verifier_sante") as mock_sante:
        mock_sante.return_value = {
            "status": "degraded",
            "database": "error: connexion",
            "upload_disk": "ok",
        }
        response = client.get("/api/health")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["database"] == "error"
