"""Sauvegardes base de données et fichiers."""

import gzip
import os
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.config import settings
from app.services import enregistrer_audit


def _backup_dir() -> str:
    path = settings.backup_dir
    os.makedirs(path, exist_ok=True)
    return path


def _pg_env() -> dict[str, str]:
    parsed = urlparse(settings.database_url)
    env = os.environ.copy()
    env.update(
        {
            "PGHOST": parsed.hostname or "db",
            "PGPORT": str(parsed.port or 5432),
            "PGUSER": parsed.username or "",
            "PGPASSWORD": parsed.password or "",
            "PGDATABASE": (parsed.path or "").lstrip("/"),
        }
    )
    return env


def lister_sauvegardes() -> list[dict]:
    repertoire = _backup_dir()
    resultats: list[dict] = []
    for nom in sorted(os.listdir(repertoire), reverse=True):
        chemin = os.path.join(repertoire, nom)
        if not os.path.isfile(chemin):
            continue
        if nom.startswith("db_") and nom.endswith(".sql.gz"):
            type_sauvegarde = "database"
        elif nom.startswith("uploads_") and nom.endswith(".tar.gz"):
            type_sauvegarde = "uploads"
        else:
            continue
        stat = os.stat(chemin)
        resultats.append(
            {
                "nom": nom,
                "type": type_sauvegarde,
                "taille_octets": stat.st_size,
                "date": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            }
        )
    return resultats


def chemin_sauvegarde(nom: str) -> str:
    if ".." in nom or "/" in nom or "\\" in nom:
        raise ValueError("Nom de fichier invalide.")
    chemin = os.path.join(_backup_dir(), nom)
    if not os.path.isfile(chemin):
        raise ValueError("Sauvegarde introuvable.")
    return chemin


def creer_sauvegarde(db, user_id: int | None) -> dict[str, str]:
    repertoire = _backup_dir()
    horodatage = datetime.now().strftime("%Y-%m-%d_%H%M")
    fichier_db = os.path.join(repertoire, f"db_{horodatage}.sql.gz")
    fichier_uploads = os.path.join(repertoire, f"uploads_{horodatage}.tar.gz")

    env = _pg_env()
    with subprocess.Popen(
        ["pg_dump", "--no-owner", "--no-acl", "--clean", "--if-exists"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as proc:
        assert proc.stdout is not None
        with gzip.open(fichier_db, "wb") as gz:
            shutil.copyfileobj(proc.stdout, gz)
        stderr = proc.stderr.read().decode() if proc.stderr else ""
        code = proc.wait()
        if code != 0:
            raise RuntimeError(f"Échec pg_dump : {stderr or code}")

    if os.path.isdir(settings.upload_dir):
        with tarfile.open(fichier_uploads, "w:gz") as tar:
            tar.add(settings.upload_dir, arcname="uploads")

    enregistrer_audit(
        db,
        user_id,
        "sauvegarde_manuelle",
        f"db_{horodatage}.sql.gz, uploads_{horodatage}.tar.gz",
        "systeme",
    )
    db.commit()

    return {
        "database": os.path.basename(fichier_db),
        "uploads": os.path.basename(fichier_uploads),
    }


def restaurer_sauvegarde(db, user_id: int | None, nom_fichier_db: str) -> None:
    if not nom_fichier_db.startswith("db_") or not nom_fichier_db.endswith(".sql.gz"):
        raise ValueError("Seuls les fichiers db_*.sql.gz peuvent être restaurés.")

    chemin = chemin_sauvegarde(nom_fichier_db)
    env = _pg_env()

    with gzip.open(chemin, "rb") as gz:
        sql_data = gz.read()

    proc = subprocess.run(
        ["psql", "--single-transaction"],
        input=sql_data,
        env=env,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            proc.stderr.decode() or "Échec de la restauration PostgreSQL."
        )

    enregistrer_audit(
        db,
        user_id,
        "restauration_sauvegarde",
        nom_fichier_db,
        "systeme",
    )
    db.commit()
