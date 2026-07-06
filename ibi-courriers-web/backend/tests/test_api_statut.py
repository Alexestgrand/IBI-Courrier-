"""Tests API — changement de statut."""

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

    reception = User(
        nom="Recep",
        prenom="Test",
        email="recep@test.ci",
        mot_de_passe=hasher_mot_de_passe("test1234"),
        role="reception",
        actif=True,
    )
    dg = User(
        nom="DG",
        prenom="Test",
        email="dg@test.ci",
        mot_de_passe=hasher_mot_de_passe("test1234"),
        role="dg",
        actif=True,
    )
    db.add_all([reception, dg])
    db.flush()

    courrier = Courrier(
        numero="ENT-IBI-2026-0001",
        type="entrant",
        entite_id=entite.id,
        expediteur="Test",
        objet="Objet test",
        service_destinataire="Direction",
        statut="en_attente",
        urgence="normal",
        created_by=reception.id,
    )
    db.add(courrier)
    db.commit()
    db.refresh(courrier)

    yield db, courrier, reception, dg
    db.close()


@pytest.fixture
def client(db_session):
    db, _, _, _ = db_session

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _auth_header(user: User) -> dict[str, str]:
    token = creer_token_acces(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}


def test_reception_peut_transmettre(client, db_session):
    _, courrier, reception, _ = db_session
    response = client.patch(
        f"/api/courriers/{courrier.id}/statut",
        json={"nouveau_statut": "transmis"},
        headers=_auth_header(reception),
    )
    assert response.status_code == 200
    assert response.json()["statut"] == "transmis"


def test_reception_ne_peut_pas_valider(client, db_session):
    db, courrier, reception, _ = db_session
    courrier.statut = "transmis"
    db.commit()

    response = client.patch(
        f"/api/courriers/{courrier.id}/statut",
        json={"nouveau_statut": "valide"},
        headers=_auth_header(reception),
    )
    assert response.status_code == 400


def test_dg_peut_valider(client, db_session):
    db, courrier, _, dg = db_session
    courrier.statut = "transmis"
    db.commit()

    response = client.patch(
        f"/api/courriers/{courrier.id}/statut",
        json={"nouveau_statut": "valide"},
        headers=_auth_header(dg),
    )
    assert response.status_code == 200
    assert response.json()["statut"] == "valide"
