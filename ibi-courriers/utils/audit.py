"""Utilitaires d'audit applicatif."""

import sqlite3

from database import models
from database.db import get_connection


def enregistrer_audit(
    user_id: int | None,
    action: str,
    detail: str | None,
    module: str,
) -> None:
    """Enregistre une action dans audit_log."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        models.inserer_audit_log(connexion, user_id, action, detail, module)
        connexion.commit()
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de l'enregistrement de l'audit.") from erreur
    finally:
        if connexion is not None:
            connexion.close()
