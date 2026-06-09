"""Connexion SQLite et initialisation du schéma."""

import os
import sqlite3

from database import models
from utils.chemin_app import determiner_racine_projet

# Racine des donnees utilisateur (a cote de l'exe en mode PyInstaller)
RACINE_PROJET = determiner_racine_projet()
CHEMIN_DB = os.path.join(RACINE_PROJET, "courriers.db")
from utils.exports import creer_dossier_exports  # noqa: E402
from utils.fichiers import creer_dossier_uploads  # noqa: E402


def get_connection() -> sqlite3.Connection:
    """Retourne une connexion SQLite vers courriers.db."""
    try:
        connexion = sqlite3.connect(CHEMIN_DB)
        connexion.row_factory = sqlite3.Row
        connexion.execute("PRAGMA foreign_keys = ON")
        return connexion
    except sqlite3.Error as erreur:
        raise RuntimeError(
            f"Impossible de se connecter à la base de données : {CHEMIN_DB}"
        ) from erreur


def init_db() -> None:
    """Crée toutes les tables et insère les données de test si nécessaire."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        models.creer_tables(connexion)
        models.migrer_schema(connexion)
        models.inserer_donnees_test(connexion)
        connexion.commit()
        creer_dossier_uploads()
        creer_dossier_exports()
        from utils.backup import creer_dossier_backups

        creer_dossier_backups()
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de l'initialisation de la base de données.") from erreur
    finally:
        if connexion is not None:
            connexion.close()
