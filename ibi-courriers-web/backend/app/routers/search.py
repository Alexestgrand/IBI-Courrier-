"""Routes recherche avancée."""

import csv
import io
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.auth import exiger_admin, exiger_session_complete
from app.database import get_db
from app.models import User
from app.pdf_export import generer_rapport_recherche_temporaire
from app.schemas import AuditLogResponse, CourrierListItem
from app.services import enregistrer_audit, lister_audit, rechercher_courriers

router = APIRouter(tags=["recherche"])


def _executer_recherche(db: Session, user: User, **params):
    try:
        return rechercher_courriers(db, user=user, **params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/recherche", response_model=list[CourrierListItem])
def get_recherche(
    mot_cle: str | None = None,
    type_courrier: str | None = None,
    statut: str | None = None,
    service: str | None = None,
    urgence: str | None = None,
    entite_id: int | None = None,
    date_debut: str | None = None,
    date_fin: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(exiger_session_complete),
):
    return _executer_recherche(
        db,
        user,
        mot_cle=mot_cle,
        type_courrier=type_courrier,
        statut=statut,
        service=service,
        urgence=urgence,
        entite_id=entite_id,
        date_debut=date_debut,
        date_fin=date_fin,
    )


@router.get("/recherche/export-pdf")
def export_recherche_pdf(
    mot_cle: str | None = None,
    type_courrier: str | None = None,
    statut: str | None = None,
    service: str | None = None,
    urgence: str | None = None,
    entite_id: int | None = None,
    date_debut: str | None = None,
    date_fin: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(exiger_session_complete),
):
    filtres = {
        "mot_cle": mot_cle,
        "type_courrier": type_courrier,
        "statut": statut,
        "service": service,
        "urgence": urgence,
        "entite_id": entite_id,
        "date_debut": date_debut,
        "date_fin": date_fin,
    }
    resultats = _executer_recherche(
        db,
        user,
        mot_cle=mot_cle,
        type_courrier=type_courrier,
        statut=statut,
        service=service,
        urgence=urgence,
        entite_id=entite_id,
        date_debut=date_debut,
        date_fin=date_fin,
    )
    if not resultats:
        raise HTTPException(status_code=400, detail="Aucun résultat à exporter.")

    chemin = generer_rapport_recherche_temporaire(resultats, filtres)
    enregistrer_audit(
        db,
        user.id,
        "export_rapport_recherche",
        f"{len(resultats)} courrier(s)",
        "recherche",
    )
    db.commit()

    return FileResponse(
        chemin,
        filename=f"rapport_recherche_{os.path.basename(chemin)}",
        media_type="application/pdf",
    )


@router.get("/recherche/export-csv")
def export_recherche_csv(
    mot_cle: str | None = None,
    type_courrier: str | None = None,
    statut: str | None = None,
    service: str | None = None,
    urgence: str | None = None,
    entite_id: int | None = None,
    date_debut: str | None = None,
    date_fin: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(exiger_session_complete),
):
    resultats = _executer_recherche(
        db,
        user,
        mot_cle=mot_cle,
        type_courrier=type_courrier,
        statut=statut,
        service=service,
        urgence=urgence,
        entite_id=entite_id,
        date_debut=date_debut,
        date_fin=date_fin,
    )
    if not resultats:
        raise HTTPException(status_code=400, detail="Aucun résultat à exporter.")

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(
        [
            "Numéro",
            "Type",
            "Contact",
            "Objet",
            "Service",
            "Urgence",
            "Statut",
            "Date",
        ]
    )
    for c in resultats:
        contact = c.get("expediteur") if c.get("type") == "entrant" else c.get("destinataire")
        writer.writerow(
            [
                c.get("numero"),
                c.get("type"),
                contact,
                c.get("objet"),
                c.get("service_destinataire") or c.get("service_emetteur"),
                c.get("urgence"),
                c.get("statut"),
                c.get("created_at"),
            ]
        )

    enregistrer_audit(
        db,
        user.id,
        "export_csv_recherche",
        f"{len(resultats)} courrier(s)",
        "recherche",
    )
    db.commit()

    contenu = buffer.getvalue()
    return StreamingResponse(
        iter([contenu]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=rapport_recherche.csv"},
    )


@router.get("/audit", response_model=list[AuditLogResponse])
def get_audit(
    module: str | None = None,
    limite: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(exiger_admin),
):
    return lister_audit(db, module, limite)
