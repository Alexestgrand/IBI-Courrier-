"""Gestion des pièces jointes courriers."""

import os
import shutil
from datetime import datetime

from database.db import RACINE_PROJET

DOSSIER_UPLOADS = os.path.join(RACINE_PROJET, "uploads")
EXTENSIONS_AUTORISEES = {".pdf", ".jpg", ".jpeg", ".png", ".docx"}


def creer_dossier_uploads() -> None:
    """Crée le dossier uploads s'il n'existe pas."""
    try:
        os.makedirs(DOSSIER_UPLOADS, exist_ok=True)
    except OSError as erreur:
        raise RuntimeError("Impossible de créer le dossier uploads.") from erreur


def copier_piece_jointe(chemin_source: str, numero_courrier: str) -> str:
    """Copie une pièce jointe et retourne le chemin relatif pour la DB."""
    try:
        creer_dossier_uploads()
        _, extension = os.path.splitext(chemin_source)
        extension = extension.lower()
        if extension not in EXTENSIONS_AUTORISEES:
            raise ValueError(
                f"Extension non autorisée. Formats acceptés : "
                f"{', '.join(sorted(EXTENSIONS_AUTORISEES))}"
            )

        horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom_fichier = f"{numero_courrier}_{horodatage}{extension}"
        chemin_dest = os.path.join(DOSSIER_UPLOADS, nom_fichier)
        shutil.copy2(chemin_source, chemin_dest)
        return os.path.join("uploads", nom_fichier).replace("\\", "/")
    except (OSError, shutil.Error) as erreur:
        raise RuntimeError("Échec de la copie de la pièce jointe.") from erreur


def ouvrir_fichier(chemin_relatif: str) -> None:
    """Ouvre un fichier avec l'application par défaut (Windows)."""
    try:
        chemin_absolu = os.path.join(RACINE_PROJET, chemin_relatif)
        if not os.path.isfile(chemin_absolu):
            raise FileNotFoundError("Fichier introuvable.")
        os.startfile(chemin_absolu)  # noqa: S606 — Windows uniquement
    except OSError as erreur:
        raise RuntimeError("Impossible d'ouvrir le fichier.") from erreur
