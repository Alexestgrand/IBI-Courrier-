"""Tests pagination recherche."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.auth import creer_token_acces, hasher_mot_de_passe
from app.database import Base, engine, get_db
from app.main import app
from app.models import Courrier, Entite, User


@pytest.fixture
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    entite = Entite(nom="IBI", code="IBI", actif=True)
    db.add(entite)
    db.flush()

    admin = User(
        nom="Admin",
        prenom="Test",
        email="admin@test.ci",
        mot_de_passe=hasher_mot_de_passe("test1234"),
        role="admin",
        actif=True,
    )
    db.add(admin)
    db.flush()

    for i in range(30):
        db.add(
            Courrier(
                numero=f"ENT-IBI-2026-{i:04d}",
                type="entrant",
                entite_id=entite.id,
                expediteur=f"Exp {i}",
                objet=f"Objet {i}",
                service_destinataire="Direction",
                statut="en_attente",
                urgence="normal",
                created_by=admin.id,
            )
        )
    db.commit()
    yield db, admin
    db.close()


@pytest.fixture
def client(db_session):
    db, _ = db_session

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {creer_token_acces(user.id, user.role)}"}


def test_recherche_paginee(client, db_session):
    _, admin = db_session
    response = client.get(
        "/api/recherche?page=1&page_size=10",
        headers=_auth(admin),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 30
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["pages"] == 3
    assert len(data["items"]) == 10


def test_recherche_page_2(client, db_session):
    _, admin = db_session
    response = client.get(
        "/api/recherche?page=2&page_size=10",
        headers=_auth(admin),
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 10


def test_recherche_filtre_mot_cle(client, db_session):
    _, admin = db_session
    response = client.get(
        "/api/recherche?mot_cle=Objet%205",
        headers=_auth(admin),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["objet"] == "Objet 5"
