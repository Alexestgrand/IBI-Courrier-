"""Tests must_change_password et configuration production."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.auth import creer_token_acces, hasher_mot_de_passe
from app.database import Base, engine, get_db
from app.main import app
from app.models import User
from app.startup_checks import valider_configuration


@pytest.fixture
def client_mdp_force():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    user = User(
        nom="Admin",
        prenom="Test",
        email="admin@test.ci",
        mot_de_passe=hasher_mot_de_passe("test1234"),
        role="admin",
        actif=True,
        must_change_password=True,
    )
    db.add(user)
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client, user
    app.dependency_overrides.clear()
    db.close()


def test_api_bloquee_si_changement_mdp_requis(client_mdp_force):
    client, user = client_mdp_force
    headers = {"Authorization": f"Bearer {creer_token_acces(user.id, user.role, user.token_version or 0)}"}

    response = client.get("/api/dashboard/stats", headers=headers)
    assert response.status_code == 403

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200

    change = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={
            "ancien_mot_de_passe": "test1234",
            "nouveau_mot_de_passe": "nouveau1234",
        },
    )
    assert change.status_code == 200

    nouveau_cookie = change.cookies.get("ibi_session")
    client.cookies.clear()
    assert client.get("/api/dashboard/stats", headers=headers).status_code == 401

    if nouveau_cookie:
        client.cookies.set("ibi_session", nouveau_cookie)
    assert client.get("/api/dashboard/stats").status_code == 200


def test_validation_secret_key_production(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "secret_key", "changez-moi-en-production")
    monkeypatch.setattr(
        settings, "database_url", "postgresql://ibi:secret@localhost/db"
    )

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        valider_configuration()


def test_validation_ok_en_developpement(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "secret_key", "changez-moi-en-production")
    valider_configuration()
