# -*- coding: utf-8 -*-
"""Chemins applicatifs : racine donnees vs assets en lecture seule (PyInstaller)."""

import os
import sys


def determiner_racine_projet() -> str:
    """Racine des donnees utilisateur (db, uploads, backups, exports)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def chemin_asset(chemin_relatif: str) -> str:
    """Assets en lecture (logo) : _MEIPASS si frozen, sinon racine projet."""
    chemin_relatif = chemin_relatif.replace("\\", "/")
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, chemin_relatif)  # type: ignore[attr-defined]
    return os.path.join(determiner_racine_projet(), chemin_relatif)


def get_resource_path(chemin_relatif: str) -> str:
    """Alias pour les vues (login, dashboard)."""
    return chemin_asset(chemin_relatif)
