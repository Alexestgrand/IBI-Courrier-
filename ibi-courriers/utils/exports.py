"""Gestion du dossier exports (PDF courriers sortants)."""

import os

from database.db import RACINE_PROJET

DOSSIER_EXPORTS = os.path.join(RACINE_PROJET, "exports")


def creer_dossier_exports() -> None:
    """Crée le dossier exports s'il n'existe pas."""
    try:
        os.makedirs(DOSSIER_EXPORTS, exist_ok=True)
    except OSError as erreur:
        raise RuntimeError("Impossible de créer le dossier exports.") from erreur


def chemin_absolu_export(chemin_relatif: str) -> str:
    """Retourne le chemin absolu d'un fichier export."""
    return os.path.join(RACINE_PROJET, chemin_relatif.replace("\\", "/"))


def ouvrir_fichier_export(chemin_relatif: str) -> None:
    """Ouvre un PDF export avec l'application par défaut (Windows)."""
    try:
        chemin_absolu = chemin_absolu_export(chemin_relatif)
        if not os.path.isfile(chemin_absolu):
            raise FileNotFoundError("Fichier export introuvable.")
        os.startfile(chemin_absolu)  # noqa: S606 — Windows uniquement
    except OSError as erreur:
        raise RuntimeError("Impossible d'ouvrir le fichier export.") from erreur
