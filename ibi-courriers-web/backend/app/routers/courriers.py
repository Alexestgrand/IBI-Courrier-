"""Routes courriers, référentiels et tableau de bord."""

import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from app.auth import obtenir_utilisateur_courant
from app.database import get_db
from app.models import Courrier, PieceJointe, User
from app.schemas import (
    ChangementStatutRequest,
    CourrierDetail,
    CourrierListItem,
    DashboardStats,
    EntiteResponse,
    ServiceResponse,
    StatutLogResponse,
)
from app.services import (
    changer_statut_courrier,
    courrier_vers_detail,
    creer_courrier_entrant,
    lister_courriers,
    lister_entites,
    lister_services,
    obtenir_historique,
    stats_dashboard,
)

router = APIRouter(tags=["courriers"])


@router.get("/entites", response_model=list[EntiteResponse])
def get_entites(
    db: Session = Depends(get_db),
    _: User = Depends(obtenir_utilisateur_courant),
):
    return lister_entites(db)


@router.get("/services", response_model=list[ServiceResponse])
def get_services(
    db: Session = Depends(get_db),
    _: User = Depends(obtenir_utilisateur_courant),
):
    return lister_services(db)


@router.get("/dashboard/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    _: User = Depends(obtenir_utilisateur_courant),
):
    return stats_dashboard(db)


@router.get("/courriers/entrants", response_model=list[CourrierListItem])
def get_courriers_entrants(
    statut: str | None = None,
    recherche: str | None = None,
    entite_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(obtenir_utilisateur_courant),
):
    return lister_courriers(db, "entrant", statut, recherche, entite_id)


@router.post("/courriers/entrants", response_model=CourrierDetail, status_code=201)
async def post_courrier_entrant(
    entite_id: int = Form(...),
    expediteur: str = Form(...),
    objet: str = Form(...),
    service_destinataire: str = Form(...),
    date_reception: str | None = Form(None),
    reference_document: str | None = Form(None),
    urgence: str = Form("normal"),
    observations: str | None = Form(None),
    fichiers: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    user: User = Depends(obtenir_utilisateur_courant),
):
    try:
        courrier = await creer_courrier_entrant(
            db,
            user,
            entite_id,
            expediteur,
            objet,
            service_destinataire,
            date_reception,
            reference_document,
            urgence,
            observations,
            fichiers,
        )
        courrier = (
            db.query(Courrier)
            .options(joinedload(Courrier.entite), joinedload(Courrier.pieces_jointes))
            .filter(Courrier.id == courrier.id)
            .first()
        )
        return courrier_vers_detail(courrier, user.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/courriers/{courrier_id}", response_model=CourrierDetail)
def get_courrier(
    courrier_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(obtenir_utilisateur_courant),
):
    courrier = (
        db.query(Courrier)
        .options(joinedload(Courrier.entite), joinedload(Courrier.pieces_jointes))
        .filter(Courrier.id == courrier_id)
        .first()
    )
    if courrier is None:
        raise HTTPException(status_code=404, detail="Courrier introuvable.")
    return courrier_vers_detail(courrier, user.role)


@router.patch("/courriers/{courrier_id}/statut", response_model=CourrierDetail)
def patch_statut(
    courrier_id: int,
    data: ChangementStatutRequest,
    db: Session = Depends(get_db),
    user: User = Depends(obtenir_utilisateur_courant),
):
    try:
        courrier = changer_statut_courrier(
            db, user, courrier_id, data.nouveau_statut, data.observation
        )
        return courrier_vers_detail(courrier, user.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/courriers/{courrier_id}/historique", response_model=list[StatutLogResponse])
def get_historique(
    courrier_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(obtenir_utilisateur_courant),
):
    return obtenir_historique(db, courrier_id)


@router.get("/pieces-jointes/{piece_id}/download")
def download_piece_jointe(
    piece_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(obtenir_utilisateur_courant),
):
    pj = db.query(PieceJointe).filter(PieceJointe.id == piece_id).first()
    if pj is None or not os.path.isfile(pj.chemin_stockage):
        raise HTTPException(status_code=404, detail="Fichier introuvable.")
    return FileResponse(
        pj.chemin_stockage,
        filename=pj.nom_original,
        media_type=pj.type_mime or "application/octet-stream",
    )
