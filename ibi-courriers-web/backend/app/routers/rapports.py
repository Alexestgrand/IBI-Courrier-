"""Routes rapports (mensuel PDF)."""

import os
import tempfile
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import exiger_dg_ou_admin, obtenir_utilisateur_courant
from app.database import get_db
from app.models import User
from app.pdf_export import generer_rapport_mensuel
from app.services import enregistrer_audit, stats_rapport_mensuel

router = APIRouter(prefix="/rapports", tags=["rapports"])


@router.get("/mensuel")
def get_rapport_mensuel(
    annee: int | None = None,
    mois: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(exiger_dg_ou_admin),
):
    maintenant = datetime.now()
    annee = annee or maintenant.year
    mois = mois or maintenant.month

    try:
        stats = stats_rapport_mensuel(db, annee, mois)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    fd, chemin = tempfile.mkstemp(suffix=".pdf", prefix="rapport_mensuel_")
    os.close(fd)
    try:
        generer_rapport_mensuel(stats, chemin)
        enregistrer_audit(
            db,
            user.id,
            "export_rapport_mensuel",
            f"{annee}-{mois:02d}",
            "rapports",
        )
        db.commit()
        return FileResponse(
            chemin,
            media_type="application/pdf",
            filename=f"rapport_mensuel_{annee}_{mois:02d}.pdf",
        )
    except Exception as exc:
        if os.path.isfile(chemin):
            os.remove(chemin)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
