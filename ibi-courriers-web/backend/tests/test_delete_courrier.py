"""Tests suppression de courriers."""

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
    compta = User(
        nom="Compta",
        prenom="Test",
        email="compta@test.ci",
        mot_de_passe=hasher_mot_de_passe("test1234"),
        role="comptabilite",
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
    db.add_all([reception, compta, dg])
    db.flush()

    courrier_recep = Courrier(
        numero="ENT-IBI-2026-0001",
        type="entrant",
        entite_id=entite.id,
        expediteur="Test",
        objet="Créé par réception",
        service_destinataire="Comptabilité",
        statut="en_attente",
        urgence="normal",
        created_by=reception.id,
    )
    courrier_dg = Courrier(
        numero="ENT-IBI-2026-0002",
        type="entrant",
        entite_id=entite.id,
        expediteur="Test",
        objet="Créé par DG",
        service_destinataire="Comptabilité",
        statut="en_attente",
        urgence="normal",
        created_by=dg.id,
    )
    courrier_valide = Courrier(
        numero="ENT-IBI-2026-0003",
        type="entrant",
        entite_id=entite.id,
        expediteur="Test",
        objet="Déjà validé",
        service_destinataire="Comptabilité",
        statut="valide",
        urgence="normal",
        created_by=reception.id,
    )
    db.add_all([courrier_recep, courrier_dg, courrier_valide])
    db.commit()

    yield db, reception, compta, dg, courrier_recep, courrier_dg, courrier_valide
    db.close()


@pytest.fixture
def client(db_session):
    db, *_ = db_session

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
    return {"Authorization": f"Bearer {creer_token_acces(user.id, user.role, user.token_version or 0)}"}


def test_createur_peut_supprimer_son_courrier_en_attente(client, db_session):
    _, reception, _, _, courrier_recep, _, _ = db_session
    response = client.delete(f"/api/courriers/{courrier_recep.id}", headers=_auth(reception))
    assert response.status_code == 204
    assert client.get(f"/api/courriers/{courrier_recep.id}", headers=_auth(reception)).status_code == 404


def test_createur_ne_peut_pas_supprimer_courrier_autrui(client, db_session):
    _, reception, _, _, _, courrier_dg, _ = db_session
    response = client.delete(f"/api/courriers/{courrier_dg.id}", headers=_auth(reception))
    assert response.status_code == 403


def test_createur_ne_peut_pas_supprimer_courrier_valide(client, db_session):
    _, reception, _, _, _, _, courrier_valide = db_session
    response = client.delete(f"/api/courriers/{courrier_valide.id}", headers=_auth(reception))
    assert response.status_code == 403


def test_dg_peut_supprimer_tout_courrier(client, db_session):
    _, _, _, dg, _, courrier_dg, courrier_valide = db_session
    assert client.delete(f"/api/courriers/{courrier_dg.id}", headers=_auth(dg)).status_code == 204
    assert client.delete(f"/api/courriers/{courrier_valide.id}", headers=_auth(dg)).status_code == 204


def test_detail_expose_peut_supprimer(client, db_session):
    _, reception, _, dg, courrier_recep, courrier_dg, courrier_valide = db_session

    detail_recep = client.get(f"/api/courriers/{courrier_recep.id}", headers=_auth(reception)).json()
    assert detail_recep["peut_supprimer"] is True

    detail_autrui = client.get(f"/api/courriers/{courrier_dg.id}", headers=_auth(reception)).json()
    assert detail_autrui["peut_supprimer"] is False

    detail_valide = client.get(f"/api/courriers/{courrier_valide.id}", headers=_auth(reception)).json()
    assert detail_valide["peut_supprimer"] is False

    detail_dg = client.get(f"/api/courriers/{courrier_valide.id}", headers=_auth(dg)).json()
    assert detail_dg["peut_supprimer"] is True
