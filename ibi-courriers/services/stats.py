# -*- coding: utf-8 -*-
"""Service des statistiques applicatives."""

import sqlite3
from typing import Any

from database import models
from database.db import get_connection


def obtenir_stats_dashboard_complet() -> dict[str, Any]:
    """Retourne les statistiques completes du tableau de bord."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        return models.obtenir_stats_dashboard(connexion)
    except sqlite3.Error as erreur:
        raise RuntimeError("Echec de la recuperation des statistiques.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def obtenir_statistiques_tableau_bord() -> dict[str, int]:
    """Retourne les cartes du tableau de bord (compatibilite)."""
    return obtenir_stats_dashboard_complet()["cartes"]


def obtenir_activite_recente(limit: int = 10) -> list[dict[str, Any]]:
    """Retourne l'activite recente des courriers."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        return models.obtenir_activite_recente(connexion, limit)
    except sqlite3.Error as erreur:
        raise RuntimeError("Echec de la recuperation de l'activite.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def obtenir_stats_par_service() -> dict[str, int]:
    """Retourne les stats par service pour le mois en cours."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        return models.obtenir_stats_par_service(connexion)
    except sqlite3.Error as erreur:
        raise RuntimeError("Echec de la recuperation des stats service.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def obtenir_courriers_urgents_non_traites() -> list[dict[str, Any]]:
    """Retourne les courriers tres urgents non traites."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        return models.obtenir_courriers_urgents_non_traites(connexion)
    except sqlite3.Error as erreur:
        raise RuntimeError("Echec de la recuperation des urgents.") from erreur
    finally:
        if connexion is not None:
            connexion.close()
