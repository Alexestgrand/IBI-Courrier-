"""Tests contrôle d'accès aux courriers (IDOR)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.auth import creer_token_acces, hasher_mot_de_passe
from app.database import Base, engine, get_db
from app.main import app
from app.models import Courrier, Entite, PieceJointe, User


@pytest.fixture
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    entite = Entite(nom="IBI", code="IBI", actif=True)
    db.add(entite)
    db.flush()

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
    db.add_all([compta, dg])
    db.flush()

    courrier_compta = Courrier(
        numero="ENT-IBI-2026-0001",
        type="entrant",
        entite_id=entite.id,
        expediteur="Fournisseur A",
        objet="Facture compta",
        service_destinataire="Comptabilité",
        statut="en_attente",
        urgence="normal",
        created_by=dg.id,
    )
    courrier_marche = Courrier(
        numero="ENT-IBI-2026-0002",
        type="entrant",
        entite_id=entite.id,
        expediteur="Fournisseur B",
        objet="Marché public",
        service_destinataire="Service Marché",
        statut="en_attente",
        urgence="normal",
        created_by=dg.id,
    )
    db.add_all([courrier_compta, courrier_marche])
    db.flush()

    pj_marche = PieceJointe(
        courrier_id=courrier_marche.id,
        nom_original="secret.pdf",
        chemin_stockage="/tmp/secret_marche.pdf",
        taille_octets=10,
        type_mime="application/pdf",
        uploaded_by=dg.id,
    )
    db.add(pj_marche)
    with open("/tmp/secret_marche.pdf", "wb") as f:
        f.write(b"%PDF-1.4 test")
    db.commit()

    yield db, courrier_compta, courrier_marche, pj_marche, compta, dg
    db.close()


@pytest.fixture
def client(db_session):
    db, _, _, _, _, _ = db_session

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


def test_compta_peut_lire_son_courrier(client, db_session):
    _, courrier_compta, _, _, compta, _ = db_session
    response = client.get(f"/api/courriers/{courrier_compta.id}", headers=_auth(compta))
    assert response.status_code == 200
    assert response.json()["numero"] == courrier_compta.numero


def test_compta_ne_peut_pas_lire_courrier_autre_service(client, db_session):
    _, _, courrier_marche, _, compta, _ = db_session
    response = client.get(f"/api/courriers/{courrier_marche.id}", headers=_auth(compta))
    assert response.status_code == 403


def test_compta_ne_peut_pas_telecharger_piece_jointe_autre_service(client, db_session):
    _, _, _, pj_marche, compta, _ = db_session
    response = client.get(
        f"/api/pieces-jointes/{pj_marche.id}/download",
        headers=_auth(compta),
    )
    assert response.status_code == 403


def test_dg_peut_lire_tous_les_courriers(client, db_session):
    _, _, courrier_marche, _, _, dg = db_session
    response = client.get(f"/api/courriers/{courrier_marche.id}", headers=_auth(dg))
    assert response.status_code == 200


def test_liste_entrants_filtree_pour_compta(client, db_session):
    _, courrier_compta, courrier_marche, _, compta, _ = db_session
    response = client.get("/api/courriers/entrants", headers=_auth(compta))
    assert response.status_code == 200
    numeros = {item["numero"] for item in response.json()["items"]}
    assert courrier_compta.numero in numeros
    assert courrier_marche.numero not in numeros
