"""Routes administration (sauvegardes, paramètres)."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import exiger_admin
from app.config import settings
from app.database import get_db
from app.email_service import envoyer_email_test
from app.models import User
from app.schemas import (
    BackupItem,
    MigrationRunRequest,
    MigrationStatusResponse,
    RestoreBackupRequest,
    SmtpStatusResponse,
    TestEmailRequest,
)
from app.services import enregistrer_audit
from app.services_backup import (
    chemin_sauvegarde,
    creer_sauvegarde,
    lister_sauvegardes,
    restaurer_sauvegarde,
)
from app.services_migration import (
    enregistrer_fichier_sqlite,
    executer_migration,
    statut_migration,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/smtp", response_model=SmtpStatusResponse)
def get_smtp_status(_: User = Depends(exiger_admin)) -> SmtpStatusResponse:
    return SmtpStatusResponse(
        enabled=settings.smtp_enabled,
        host=settings.smtp_host if settings.smtp_enabled else None,
        from_address=settings.smtp_from if settings.smtp_enabled else None,
    )


@router.post("/smtp/test")
def post_smtp_test(
    data: TestEmailRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(exiger_admin),
) -> dict[str, str]:
    try:
        envoyer_email_test(data.email)
        enregistrer_audit(db, admin.id, "test_email_smtp", data.email, "systeme")
        db.commit()
        return {"message": f"E-mail de test envoyé à {data.email}."}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/backups", response_model=list[BackupItem])
def get_backups(_: User = Depends(exiger_admin)) -> list[dict]:
    return lister_sauvegardes()


@router.post("/backups")
def post_backup(
    db: Session = Depends(get_db),
    admin: User = Depends(exiger_admin),
) -> dict:
    try:
        fichiers = creer_sauvegarde(db, admin.id)
        return {"message": "Sauvegarde créée.", "fichiers": fichiers}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/backups/{nom}/download")
def download_backup(
    nom: str,
    _: User = Depends(exiger_admin),
):
    try:
        chemin = chemin_sauvegarde(nom)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    media = "application/gzip"
    if nom.endswith(".tar.gz"):
        media = "application/x-tar"
    return FileResponse(chemin, filename=nom, media_type=media)


@router.post("/backups/restore")
def post_restore_backup(
    data: RestoreBackupRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(exiger_admin),
) -> dict[str, str]:
    if data.confirmation != "RESTAURER":
        raise HTTPException(
            status_code=400,
            detail="Saisissez RESTAURER pour confirmer la restauration.",
        )
    try:
        restaurer_sauvegarde(db, admin.id, data.nom_fichier)
        return {"message": "Base de données restaurée. Rechargez l'application."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/migration", response_model=MigrationStatusResponse)
def get_migration_status(_: User = Depends(exiger_admin)) -> dict:
    return statut_migration()


@router.post("/migration/upload")
async def post_migration_upload(
    fichier: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(exiger_admin),
) -> dict[str, str]:
    if not fichier.filename or not fichier.filename.endswith(".db"):
        raise HTTPException(
            status_code=400,
            detail="Envoyez un fichier courriers.db (SQLite).",
        )
    contenu = await fichier.read()
    if len(contenu) < 1024:
        raise HTTPException(status_code=400, detail="Fichier trop petit ou vide.")
    chemin = enregistrer_fichier_sqlite(contenu)
    enregistrer_audit(
        db,
        admin.id,
        "migration_upload",
        chemin.name,
        "migration",
    )
    db.commit()
    return {"message": f"Fichier {chemin.name} enregistré ({len(contenu)} octets)."}


@router.post("/migration/run")
def post_migration_run(
    data: MigrationRunRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(exiger_admin),
) -> dict:
    try:
        stats = executer_migration(
            db,
            entite_defaut=data.entite_defaut,
            dry_run=data.dry_run,
        )
        if not data.dry_run:
            enregistrer_audit(
                db,
                admin.id,
                "migration_executee",
                str(stats),
                "migration",
            )
            db.commit()
        return {
            "message": "Simulation terminée." if data.dry_run else "Migration terminée.",
            "stats": stats,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
