# -*- coding: utf-8 -*-
"""Service metier de recherche avancee."""

import sqlite3
from datetime import datetime
from typing import Any

from database import models
from database.db import get_connection
from utils.audit import enregistrer_audit
from utils.export_pdf import generer_rapport_recherche

MODULE_RECHERCHE = "recherche"


def valider_date_jjmmaaaa(texte: str) -> datetime | None:
    """Valide une date JJ/MM/AAAA ; retourne None si vide."""
    texte = texte.strip()
    if not texte:
        return None
    try:
        return datetime.strptime(texte, "%d/%m/%Y")
    except ValueError as erreur:
        raise ValueError(
            "Date invalide : format attendu JJ/MM/AAAA."
        ) from erreur


def _date_vers_entier(texte: str) -> int | None:
    """Convertit JJ/MM/AAAA en entier YYYYMMDD."""
    date = valider_date_jjmmaaaa(texte)
    if date is None:
        return None
    return date.year * 10000 + date.month * 100 + date.day


def rechercher_courriers(filtres: dict[str, Any]) -> list[dict[str, Any]]:
    """Execute une recherche avancee selon les filtres fournis."""
    date_debut = None
    date_fin = None

    if filtres.get("date_debut"):
        date_debut = _date_vers_entier(str(filtres["date_debut"]))
    if filtres.get("date_fin"):
        date_fin = _date_vers_entier(str(filtres["date_fin"]))

    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        return models.recherche_courriers(
            connexion,
            mot_cle=filtres.get("mot_cle") or None,
            type_courrier=filtres.get("type_courrier"),
            statut=filtres.get("statut"),
            service=filtres.get("service"),
            urgence=filtres.get("urgence"),
            date_debut=date_debut,
            date_fin=date_fin,
        )
    except sqlite3.Error as erreur:
        raise RuntimeError("Echec de la recherche.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def exporter_rapport_recherche(
    resultats: list[dict[str, Any]],
    filtres_appliques: dict[str, Any],
    chemin_sortie: str,
    user_id: int,
) -> None:
    """Exporte un rapport PDF des resultats de recherche."""
    try:
        generer_rapport_recherche(resultats, filtres_appliques, chemin_sortie)
        enregistrer_audit(
            user_id,
            "export_rapport_recherche",
            f"{len(resultats)} courrier(s)",
            MODULE_RECHERCHE,
        )
    except RuntimeError:
        raise
