"""Migration des données desktop SQLite → PostgreSQL."""

from __future__ import annotations

import shutil
import sqlite3
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models import AuditLog, Courrier, Entite, PieceJointe, StatutLog, User
from app.seed import initialiser_donnees


def chemin_sqlite_defaut() -> Path:
    return Path(settings.migration_dir) / "courriers.db"


def statut_migration() -> dict:
    chemin = chemin_sqlite_defaut()
    if not chemin.is_file():
        return {"pret": False, "fichier": None, "taille_octets": 0}
    return {
        "pret": True,
        "fichier": chemin.name,
        "taille_octets": chemin.stat().st_size,
    }


def enregistrer_fichier_sqlite(contenu: bytes) -> Path:
    dossier = Path(settings.migration_dir)
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = chemin_sqlite_defaut()
    with open(chemin, "wb") as f:
        f.write(contenu)
    return chemin


def _copier_fichier(source: Path, dest_dir: Path) -> str | None:
    if not source.is_file():
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"mig_{uuid.uuid4().hex}{source.suffix}"
    shutil.copy2(source, dest)
    return str(dest)


def executer_migration(
    db: Session,
    sqlite_path: Path | None = None,
    uploads_root: Path | None = None,
    entite_defaut: str = "IBI",
    dry_run: bool = False,
) -> dict:
    sqlite_path = sqlite_path or chemin_sqlite_defaut()
    if not sqlite_path.is_file():
        raise FileNotFoundError(f"Fichier SQLite introuvable : {sqlite_path}")

    uploads_root = uploads_root or sqlite_path.parent / "uploads"
    dest_uploads = Path(settings.upload_dir)

    initialiser_donnees(db)

    entite = db.query(Entite).filter(Entite.nom == entite_defaut).first()
    if entite is None:
        raise ValueError(f"Entité « {entite_defaut} » introuvable.")

    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row

    user_map: dict[int, int] = {}
    courrier_map: dict[int, int] = {}
    stats = {"utilisateurs": 0, "courriers": 0, "pieces_jointes": 0, "historiques": 0}

    for row in conn.execute("SELECT * FROM users ORDER BY id"):
        existant = db.query(User).filter(User.email.ilike(row["email"])).first()
        if existant:
            user_map[row["id"]] = existant.id
            continue
        if dry_run:
            user_map[row["id"]] = row["id"]
            stats["utilisateurs"] += 1
            continue
        user = User(
            nom=row["nom"],
            prenom=row["prenom"],
            email=row["email"],
            mot_de_passe=row["mot_de_passe"],
            role=row["role"],
            actif=bool(row["actif"]),
        )
        db.add(user)
        db.flush()
        user_map[row["id"]] = user.id
        stats["utilisateurs"] += 1

    for row in conn.execute("SELECT * FROM courriers ORDER BY id"):
        existant = db.query(Courrier).filter(Courrier.numero == row["numero"]).first()
        if existant:
            courrier_map[row["id"]] = existant.id
            continue
        if dry_run:
            courrier_map[row["id"]] = row["id"]
            stats["courriers"] += 1
            continue

        chemin_pdf = None
        if row["chemin_pdf"]:
            src = uploads_root.parent / row["chemin_pdf"]
            if not src.is_file():
                src = uploads_root / Path(row["chemin_pdf"]).name
            chemin_pdf = _copier_fichier(src, dest_uploads / "exports")

        courrier = Courrier(
            numero=row["numero"],
            type=row["type"],
            entite_id=entite.id,
            date_reception=row["date_reception"],
            expediteur=row["expediteur"],
            reference_document=row["reference_document"],
            objet=row["objet"],
            service_destinataire=row["service_destinataire"],
            destinataire=row["destinataire"] if "destinataire" in row.keys() else None,
            adresse_destinataire=row["adresse_destinataire"]
            if "adresse_destinataire" in row.keys()
            else None,
            service_emetteur=row["service_emetteur"]
            if "service_emetteur" in row.keys()
            else None,
            corps_courrier=row["corps_courrier"] if "corps_courrier" in row.keys() else None,
            urgence=row["urgence"],
            statut=row["statut"],
            observations=row["observations"],
            chemin_pdf=chemin_pdf,
            created_by=user_map.get(row["created_by"]),
        )
        db.add(courrier)
        db.flush()
        courrier_map[row["id"]] = courrier.id
        stats["courriers"] += 1

        if row["fichier_joint"]:
            src = uploads_root / row["fichier_joint"]
            if not src.is_file():
                src = sqlite_path.parent / "uploads" / row["fichier_joint"]
            chemin = _copier_fichier(src, dest_uploads)
            if chemin:
                db.add(
                    PieceJointe(
                        courrier_id=courrier.id,
                        nom_original=row["fichier_joint"],
                        chemin_stockage=chemin,
                        taille_octets=Path(chemin).stat().st_size,
                        uploaded_by=user_map.get(row["created_by"]),
                    )
                )
                stats["pieces_jointes"] += 1

    for row in conn.execute("SELECT * FROM statuts_log ORDER BY id"):
        if dry_run:
            stats["historiques"] += 1
            continue
        cid = courrier_map.get(row["courrier_id"])
        if not cid:
            continue
        db.add(
            StatutLog(
                courrier_id=cid,
                ancien_statut=row["ancien_statut"],
                nouveau_statut=row["nouveau_statut"],
                user_id=user_map.get(row["user_id"]),
                observation=row["observation"],
            )
        )
        stats["historiques"] += 1

    for row in conn.execute("SELECT * FROM audit_log ORDER BY id"):
        if dry_run:
            continue
        db.add(
            AuditLog(
                user_id=user_map.get(row["user_id"]),
                action=row["action"],
                detail=row["detail"],
                module=row["module"],
            )
        )

    conn.close()

    if not dry_run:
        db.commit()

    return stats
