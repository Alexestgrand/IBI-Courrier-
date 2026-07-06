"""Routes courriers, référentiels et tableau de bord."""

import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from app.auth import exiger_dg_ou_admin, exiger_session_complete
from app.authorization import obtenir_courrier_autorise, obtenir_piece_jointe_autorisee
from app.database import get_db
from app.models import Courrier, User
from app.schemas import (
    ChangementStatutRequest,
    CourrierDetail,
    CourrierListItem,
    CourrierUpdateRequest,
    DashboardStats,
    PaginatedCourriersResponse,
    EntiteResponse,
    ServiceResponse,
    StatutLogResponse,
)
from app.services import (
    changer_statut_courrier,
    courrier_vers_detail,
    creer_courrier_entrant,
    creer_courrier_sortant,
    lister_a_valider,
    lister_courriers,
    lister_entites,
    lister_services,
    modifier_courrier,
    obtenir_historique,
    signer_courrier_sortant,
    stats_dashboard,
)

router = APIRouter(tags=["courriers"])


@router.get("/entites", response_model=list[EntiteResponse])
def get_entites(
    db: Session = Depends(get_db),
    _: User = Depends(exiger_session_complete),
):
    return lister_entites(db)


@router.get("/services", response_model=list[ServiceResponse])
def get_services(
    db: Session = Depends(get_db),
    _: User = Depends(exiger_session_complete),
):
    return lister_services(db)


@router.get("/dashboard/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    user: User = Depends(exiger_session_complete),
):
    return stats_dashboard(db, user)


@router.get("/courriers/a-valider", response_model=PaginatedCourriersResponse)
def get_courriers_a_valider(
    page: int = 1,
    page_size: int = 25,
    db: Session = Depends(get_db),
    _: User = Depends(exiger_dg_ou_admin),
):
    return lister_a_valider(db, page, page_size)


@router.get("/courriers/sortants", response_model=PaginatedCourriersResponse)
def get_courriers_sortants(
    statut: str | None = None,
    recherche: str | None = None,
    entite_id: int | None = None,
    service: str | None = None,
    mon_service: bool = False,
    page: int = 1,
    page_size: int = 25,
    db: Session = Depends(get_db),
    user: User = Depends(exiger_session_complete),
):
    return lister_courriers(
        db,
        "sortant",
        statut,
        recherche,
        entite_id,
        service,
        mon_service,
        user.role,
        page,
        page_size,
    )


@router.post("/courriers/sortants", response_model=CourrierDetail, status_code=201)
async def post_courrier_sortant(
    entite_id: int = Form(...),
    destinataire: str = Form(...),
    objet: str = Form(...),
    service_emetteur: str = Form(...),
    adresse_destinataire: str | None = Form(None),
    urgence: str = Form("normal"),
    observations: str | None = Form(None),
    corps_courrier: str | None = Form(None),
    pdf_scanne: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(exiger_session_complete),
):
    try:
        courrier = await creer_courrier_sortant(
            db,
            user,
            entite_id,
            destinataire,
            objet,
            service_emetteur,
            adresse_destinataire,
            urgence,
            observations,
            corps_courrier,
            pdf_scanne,
        )
        courrier = (
            db.query(Courrier)
            .options(
            joinedload(Courrier.entite),
            joinedload(Courrier.pieces_jointes),
            joinedload(Courrier.signataire),
        )
            .filter(Courrier.id == courrier.id)
            .first()
        )
        return courrier_vers_detail(courrier, user.role, user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/courriers/entrants", response_model=PaginatedCourriersResponse)
def get_courriers_entrants(
    statut: str | None = None,
    recherche: str | None = None,
    entite_id: int | None = None,
    service: str | None = None,
    mon_service: bool = False,
    page: int = 1,
    page_size: int = 25,
    db: Session = Depends(get_db),
    user: User = Depends(exiger_session_complete),
):
    return lister_courriers(
        db,
        "entrant",
        statut,
        recherche,
        entite_id,
        service,
        mon_service,
        user.role,
        page,
        page_size,
    )


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
    user: User = Depends(exiger_session_complete),
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
            .options(
            joinedload(Courrier.entite),
            joinedload(Courrier.pieces_jointes),
            joinedload(Courrier.signataire),
        )
            .filter(Courrier.id == courrier.id)
            .first()
        )
        return courrier_vers_detail(courrier, user.role, user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/courriers/{courrier_id}", response_model=CourrierDetail)
def get_courrier(
    courrier_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(exiger_session_complete),
):
    courrier = obtenir_courrier_autorise(db, courrier_id, user)
    return courrier_vers_detail(courrier, user.role, user)


@router.patch("/courriers/{courrier_id}", response_model=CourrierDetail)
def patch_courrier(
    courrier_id: int,
    data: CourrierUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(exiger_session_complete),
):
    try:
        champs = data.model_dump(exclude_unset=True)
        courrier = modifier_courrier(db, user, courrier_id, champs)
        return courrier_vers_detail(courrier, user.role, user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/courriers/{courrier_id}/statut", response_model=CourrierDetail)
def patch_statut(
    courrier_id: int,
    data: ChangementStatutRequest,
    db: Session = Depends(get_db),
    user: User = Depends(exiger_session_complete),
):
    try:
        courrier = changer_statut_courrier(
            db, user, courrier_id, data.nouveau_statut, data.observation
        )
        return courrier_vers_detail(courrier, user.role, user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/courriers/{courrier_id}/signer", response_model=CourrierDetail)
def post_signer_courrier(
    courrier_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(exiger_session_complete),
):
    try:
        courrier = signer_courrier_sortant(db, user, courrier_id)
        courrier = (
            db.query(Courrier)
            .options(
                joinedload(Courrier.entite),
                joinedload(Courrier.pieces_jointes),
                joinedload(Courrier.signataire),
            )
            .filter(Courrier.id == courrier.id)
            .first()
        )
        return courrier_vers_detail(courrier, user.role, user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/courriers/{courrier_id}/historique", response_model=list[StatutLogResponse])
def get_historique(
    courrier_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(exiger_session_complete),
):
    obtenir_courrier_autorise(db, courrier_id, user, avec_relations=False)
    return obtenir_historique(db, courrier_id)


@router.get("/courriers/{courrier_id}/pdf")
def download_pdf_courrier(
    courrier_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(exiger_session_complete),
):
    courrier = obtenir_courrier_autorise(db, courrier_id, user)
    if courrier.type != "sortant":
        raise HTTPException(status_code=400, detail="PDF disponible uniquement pour les sortants.")

    chemin = courrier.chemin_pdf
    if not chemin or not os.path.isfile(chemin):
        from app.config import settings
        from app.pdf_export import generer_pdf_sortant

        exports_dir = os.path.join(settings.upload_dir, "exports")
        os.makedirs(exports_dir, exist_ok=True)
        chemin = os.path.join(exports_dir, f"{courrier.numero}.pdf")
        generer_pdf_sortant(courrier_vers_detail(courrier, user.role), chemin)
        courrier.chemin_pdf = chemin
        db.commit()

    return FileResponse(
        chemin,
        filename=f"{courrier.numero}.pdf",
        media_type="application/pdf",
    )


@router.get("/pieces-jointes/{piece_id}/view")
def view_piece_jointe(
    piece_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(exiger_session_complete),
):
    pj = obtenir_piece_jointe_autorisee(db, piece_id, user)
    if not os.path.isfile(pj.chemin_stockage):
        raise HTTPException(status_code=404, detail="Fichier introuvable.")
    return FileResponse(
        pj.chemin_stockage,
        filename=pj.nom_original,
        media_type=pj.type_mime or "application/octet-stream",
        content_disposition_type="inline",
    )


@router.get("/pieces-jointes/{piece_id}/download")
def download_piece_jointe(
    piece_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(exiger_session_complete),
):
    pj = obtenir_piece_jointe_autorisee(db, piece_id, user)
    if not os.path.isfile(pj.chemin_stockage):
        raise HTTPException(status_code=404, detail="Fichier introuvable.")
    return FileResponse(
        pj.chemin_stockage,
        filename=pj.nom_original,
        media_type=pj.type_mime or "application/octet-stream",
    )
