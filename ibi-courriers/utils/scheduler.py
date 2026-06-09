# -*- coding: utf-8 -*-
"""Planification des taches automatiques (sans mise a jour UI)."""

import threading
from datetime import datetime, timedelta

from utils.backup import clean_old_backups, create_backup

_timers: list[threading.Timer] = []
_backup_auto_actif: bool = True
_nettoyage_auto_actif: bool = True
_prochain_backup: datetime | None = None
_timer_backup: threading.Timer | None = None
_timer_nettoyage: threading.Timer | None = None


def get_prochaine_sauvegarde() -> datetime | None:
    """Retourne la date/heure de la prochaine sauvegarde automatique."""
    return _prochain_backup


def get_backup_auto_actif() -> bool:
    return _backup_auto_actif


def get_nettoyage_auto_actif() -> bool:
    return _nettoyage_auto_actif


def set_backup_auto_actif(actif: bool) -> None:
    """Active ou desactive la sauvegarde quotidienne automatique."""
    global _backup_auto_actif, _prochain_backup
    _backup_auto_actif = actif
    if not actif and _timer_backup is not None:
        _timer_backup.cancel()
        _prochain_backup = None
    elif actif:
        _planifier_backup_quotidien()


def set_nettoyage_auto_actif(actif: bool) -> None:
    """Active ou desactive le nettoyage hebdomadaire."""
    global _nettoyage_auto_actif
    _nettoyage_auto_actif = actif
    if not actif and _timer_nettoyage is not None:
        _timer_nettoyage.cancel()


def _secondes_jusqu_a_minuit() -> float:
    maintenant = datetime.now()
    demain = (maintenant + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return (demain - maintenant).total_seconds()


def _executer_backup_auto() -> None:
    try:
        create_backup(user_id=None)
    except RuntimeError:
        pass
    _planifier_backup_quotidien()


def _executer_nettoyage_auto() -> None:
    try:
        clean_old_backups()
    except RuntimeError:
        pass
    _planifier_nettoyage_hebdo()


def _planifier_backup_quotidien() -> None:
    """Planifie la prochaine sauvegarde a minuit."""
    global _prochain_backup, _timer_backup

    if not _backup_auto_actif:
        _prochain_backup = None
        return

    delai = _secondes_jusqu_a_minuit()
    _prochain_backup = datetime.now() + timedelta(seconds=delai)

    _timer_backup = threading.Timer(delai, _executer_backup_auto)
    _timer_backup.daemon = True
    _timers.append(_timer_backup)
    _timer_backup.start()


def _planifier_nettoyage_hebdo() -> None:
    """Planifie le nettoyage hebdomadaire."""
    # Tache hebdomadaire = purge (clean_old_backups), pas backup hebdomadaire.
    global _timer_nettoyage

    if not _nettoyage_auto_actif:
        return

    delai = 7 * 24 * 3600
    _timer_nettoyage = threading.Timer(delai, _executer_nettoyage_auto)
    _timer_nettoyage.daemon = True
    _timers.append(_timer_nettoyage)
    _timer_nettoyage.start()


def start_scheduler() -> None:
    """Demarre les taches planifiees (sans reference UI)."""
    _planifier_backup_quotidien()
    _planifier_nettoyage_hebdo()


def arreter_scheduler() -> None:
    """Annule tous les timers en cours."""
    global _prochain_backup
    for timer in _timers:
        try:
            timer.cancel()
        except Exception:
            pass
    _timers.clear()
    _prochain_backup = None
