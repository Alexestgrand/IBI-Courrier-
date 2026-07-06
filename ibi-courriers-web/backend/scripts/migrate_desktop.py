#!/usr/bin/env python3
"""
Migration des données desktop (SQLite) vers PostgreSQL.

Usage :
  python scripts/migrate_desktop.py \\
    --sqlite /chemin/vers/courriers.db \\
    --uploads /chemin/vers/uploads \\
    --database-url postgresql://ibi:pass@localhost:5432/ibi_courriers

Depuis le VPS (avec accès au volume Docker) :
  docker compose -f docker-compose.prod.yml exec backend \\
    python /app/scripts/migrate_desktop.py --sqlite /data/migration/courriers.db
"""

from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Permet l'exécution depuis la racine du projet
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.config import settings  # noqa: E402
from app.models import AuditLog, Courrier, Entite, PieceJointe, StatutLog, User  # noqa: E402
from app.seed import initialiser_donnees  # noqa: E402


def parser_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Migration SQLite desktop → PostgreSQL")
    p.add_argument("--sqlite", required=True, help="Chemin vers courriers.db")
    p.add_argument(
        "--uploads",
        default=None,
        help="Dossier uploads/ desktop (fichiers joints et PDF)",
    )
    p.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", settings.database_url),
        help="URL PostgreSQL",
    )
    p.add_argument(
        "--entite-defaut",
        default="IBI",
        help="Filiale par défaut pour les courriers sans entité",
    )
    p.add_argument("--dry-run", action="store_true", help="Simulation sans écriture")
    return p.parse_args()


def copier_fichier(source: Path, dest_dir: Path) -> str | None:
    if not source.is_file():
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"mig_{uuid.uuid4().hex}{source.suffix}"
    shutil.copy2(source, dest)
    return str(dest)


def main() -> None:
    args = parser_args()
    sqlite_path = Path(args.sqlite)
    if not sqlite_path.is_file():
        print(f"Fichier SQLite introuvable : {sqlite_path}")
        sys.exit(1)

    uploads_root = Path(args.uploads) if args.uploads else sqlite_path.parent / "uploads"
    dest_uploads = Path(settings.upload_dir)

    engine = create_engine(args.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db: Session = SessionLocal()

    initialiser_donnees(db)

    entite = db.query(Entite).filter(Entite.nom == args.entite_defaut).first()
    if entite is None:
        print(f"Entité « {args.entite_defaut} » introuvable.")
        sys.exit(1)

    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row

    user_map: dict[int, int] = {}
    courrier_map: dict[int, int] = {}

    print("Migration des utilisateurs…")
    for row in conn.execute("SELECT * FROM users ORDER BY id"):
        existant = db.query(User).filter(User.email.ilike(row["email"])).first()
        if existant:
            user_map[row["id"]] = existant.id
            continue
        if args.dry_run:
            user_map[row["id"]] = row["id"]
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

    print("Migration des courriers…")
    for row in conn.execute("SELECT * FROM courriers ORDER BY id"):
        existant = db.query(Courrier).filter(Courrier.numero == row["numero"]).first()
        if existant:
            courrier_map[row["id"]] = existant.id
            continue
        if args.dry_run:
            courrier_map[row["id"]] = row["id"]
            continue

        chemin_pdf = None
        if row["chemin_pdf"]:
            src = uploads_root.parent / row["chemin_pdf"]
            if not src.is_file():
                src = uploads_root / Path(row["chemin_pdf"]).name
            chemin_pdf = copier_fichier(src, dest_uploads / "exports")

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

        if row["fichier_joint"]:
            src = uploads_root / row["fichier_joint"]
            if not src.is_file():
                src = sqlite_path.parent / "uploads" / row["fichier_joint"]
            chemin = copier_fichier(src, dest_uploads)
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

    print("Migration des historiques de statut…")
    for row in conn.execute("SELECT * FROM statuts_log ORDER BY id"):
        if args.dry_run:
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

    print("Migration du journal d'audit…")
    for row in conn.execute("SELECT * FROM audit_log ORDER BY id"):
        if args.dry_run:
            continue
        db.add(
            AuditLog(
                user_id=user_map.get(row["user_id"]),
                action=row["action"],
                detail=row["detail"],
                module=row["module"],
            )
        )

    if args.dry_run:
        print("Dry-run terminé — aucune donnée écrite.")
    else:
        db.commit()
        print(
            f"Migration terminée : {len(user_map)} utilisateurs, "
            f"{len(courrier_map)} courriers."
        )

    conn.close()
    db.close()


if __name__ == "__main__":
    main()
