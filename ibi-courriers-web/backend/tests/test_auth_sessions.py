"""Tests sessions JWT (cookies, révocation)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.auth import creer_token_acces, hasher_mot_de_passe
from app.config import settings
from app.database import Base, engine, get_db
from app.main import app
from app.models import User


@pytest.fixture
def client_auth():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    user = User(
        nom="User",
        prenom="Test",
        email="user@test.ci",
        mot_de_passe=hasher_mot_de_passe("secret123"),
        role="reception",
        actif=True,
        token_version=0,
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
        yield test_client, user, db
    app.dependency_overrides.clear()
    db.close()


def test_login_definit_cookie_httponly(client_auth):
    client, user, _db = client_auth
    response = client.post(
        "/api/auth/login",
        json={"email": user.email, "mot_de_passe": "secret123"},
    )
    assert response.status_code == 200
    assert response.json()["must_change_password"] is False
    assert settings.cookie_name in response.cookies
    assert client.get("/api/auth/me").status_code == 200


def test_logout_revoque_la_session(client_auth):
    client, user, db = client_auth
    client.post("/api/auth/login", json={"email": user.email, "mot_de_passe": "secret123"})
    assert client.get("/api/auth/me").status_code == 200

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert client.get("/api/auth/me").status_code == 401

    db.refresh(user)
    assert user.token_version == 1


def test_ancien_token_invalide_apres_revoque(client_auth):
    client, user, db = client_auth
    ancien = creer_token_acces(user.id, user.role, user.token_version or 0)
    user.token_version = 1
    db.commit()

    headers = {"Authorization": f"Bearer {ancien}"}
    assert client.get("/api/auth/me", headers=headers).status_code == 401
