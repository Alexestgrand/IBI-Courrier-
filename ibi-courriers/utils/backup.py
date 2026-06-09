# -*- coding: utf-8 -*-
"""Sauvegarde et restauration de la base de donnees et des fichiers."""

import os
import re
import shutil
from datetime import datetime
from typing import Any

from database import models
from database.db import CHEMIN_DB, RACINE_PROJET, get_connection
from utils.audit import enregistrer_audit
from utils.exports import DOSSIER_EXPORTS, creer_dossier_exports
from utils.fichiers import DOSSIER_UPLOADS, creer_dossier_uploads

DOSSIER_BACKUPS = os.path.join(RACINE_PROJET, "backups")
SOUS_DOSSIER_SECURITE = "_pre_restore"
MODULE_SYSTEME = "systeme"

_FORMAT_DOSSIER = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$")


def creer_dossier_backups() -> None:
    """Cree le dossier backups s'il n'existe pas."""
    try:
        os.makedirs(DOSSIER_BACKUPS, exist_ok=True)
    except OSError as erreur:
        raise RuntimeError("Impossible de creer le dossier backups.") from erreur


def chemin_dossier_backups() -> str:
    """Retourne le chemin absolu du dossier backups."""
    return DOSSIER_BACKUPS


def _calculer_taille_et_fichiers(chemin: str) -> tuple[int, int]:
    """Retourne la taille totale (octets) et le nombre de fichiers."""
    taille = 0
    nb_fichiers = 0
    for racine, _dossiers, fichiers in os.walk(chemin):
        for nom in fichiers:
            nb_fichiers += 1
            try:
                taille += os.path.getsize(os.path.join(racine, nom))
            except OSError:
                pass
    return taille, nb_fichiers


def _nom_dossier_backup() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _est_sous_dossier_backups(chemin: str) -> str:
    """Valide qu'un chemin est sous DOSSIER_BACKUPS (anti path traversal)."""
    racine = os.path.realpath(DOSSIER_BACKUPS)
    chemin_absolu = os.path.realpath(chemin)
    if not chemin_absolu.startswith(racine + os.sep) and chemin_absolu != racine:
        raise RuntimeError("Chemin de sauvegarde invalide.")
    return chemin_absolu


def _contient_pre_restore(chemin: str) -> bool:
    parties = os.path.normpath(chemin).split(os.sep)
    return SOUS_DOSSIER_SECURITE in parties


def _parser_nom_dossier(nom: str) -> tuple[str, str]:
    """Extrait date et heure depuis le nom du dossier backup."""
    if _FORMAT_DOSSIER.match(nom):
        date_part, heure_part = nom.split("_", 1)
        heure = heure_part.replace("-", ":")
        return date_part, heure
    return nom, ""


def _ecrire_backup_info(
    chemin_backup: str,
    dossiers_copies: list[str],
    nb_courriers: int,
) -> None:
    maintenant = datetime.now()
    taille, _ = _calculer_taille_et_fichiers(chemin_backup)
    lignes = [
        f"Date : {maintenant.strftime('%d/%m/%Y')}",
        f"Heure : {maintenant.strftime('%H:%M:%S')}",
        f"Nombre de courriers : {nb_courriers}",
        f"Taille totale (octets) : {taille}",
        f"Dossiers copies : {', '.join(dossiers_copies)}",
    ]
    chemin_info = os.path.join(chemin_backup, "backup_info.txt")
    with open(chemin_info, "w", encoding="utf-8") as fichier:
        fichier.write("\n".join(lignes))


def _executer_copie_backup(
    chemin_backup: str,
    user_id: int | None,
    *,
    enregistrer_journal: bool = True,
    detail_audit: str | None = None,
) -> str:
    """Copie db, uploads et exports vers un dossier backup existant."""
    dossiers_copies: list[str] = ["courriers.db"]

    shutil.copy2(CHEMIN_DB, os.path.join(chemin_backup, "courriers.db"))

    if os.path.isdir(DOSSIER_UPLOADS):
        shutil.copytree(
            DOSSIER_UPLOADS,
            os.path.join(chemin_backup, "uploads"),
            dirs_exist_ok=True,
        )
        dossiers_copies.append("uploads")

    if os.path.isdir(DOSSIER_EXPORTS):
        shutil.copytree(
            DOSSIER_EXPORTS,
            os.path.join(chemin_backup, "exports"),
            dirs_exist_ok=True,
        )
        dossiers_copies.append("exports")

    connexion = None
    try:
        connexion = get_connection()
        nb_courriers = models.compter_courriers(connexion)
    except Exception:
        nb_courriers = 0
    finally:
        if connexion is not None:
            connexion.close()

    _ecrire_backup_info(chemin_backup, dossiers_copies, nb_courriers)

    nom_dossier = detail_audit or os.path.basename(chemin_backup)
    if enregistrer_journal:
        enregistrer_audit(
            user_id,
            "sauvegarde_creee",
            nom_dossier,
            MODULE_SYSTEME,
        )

    return chemin_backup


def create_backup(
    user_id: int | None = None,
    *,
    securite_pre_restore: bool = False,
) -> str:
    """Cree une sauvegarde complete et retourne le chemin du dossier."""
    try:
        creer_dossier_backups()
        nom = _nom_dossier_backup()
        if securite_pre_restore:
            parent = os.path.join(DOSSIER_BACKUPS, SOUS_DOSSIER_SECURITE)
            os.makedirs(parent, exist_ok=True)
            chemin_backup = os.path.join(parent, nom)
        else:
            chemin_backup = os.path.join(DOSSIER_BACKUPS, nom)

        os.makedirs(chemin_backup, exist_ok=False)
        return _executer_copie_backup(
            chemin_backup,
            user_id,
            enregistrer_journal=True,
            detail_audit=(
                f"{SOUS_DOSSIER_SECURITE}/{nom}"
                if securite_pre_restore
                else nom
            ),
        )
    except (OSError, shutil.Error) as erreur:
        raise RuntimeError("Echec de la creation de la sauvegarde.") from erreur


def _backup_vers_dict(chemin: str) -> dict[str, Any]:
    nom = os.path.basename(chemin)
    date_str, heure_str = _parser_nom_dossier(nom)
    taille, nb_fichiers = _calculer_taille_et_fichiers(chemin)
    return {
        "chemin": chemin,
        "nom": nom,
        "date": date_str,
        "heure": heure_str,
        "taille_octets": taille,
        "nb_fichiers": nb_fichiers,
    }


def _est_dossier_backup_valide(chemin: str, nom: str) -> bool:
    if nom == SOUS_DOSSIER_SECURITE:
        return False
    if os.path.isfile(os.path.join(chemin, "courriers.db")):
        return True
    return bool(_FORMAT_DOSSIER.match(nom))


def get_liste_backups() -> list[dict[str, Any]]:
    """Liste les sauvegardes disponibles, plus recentes en premier."""
    if not os.path.isdir(DOSSIER_BACKUPS):
        return []

    sauvegardes: list[dict[str, Any]] = []
    try:
        for nom in os.listdir(DOSSIER_BACKUPS):
            if nom == SOUS_DOSSIER_SECURITE:
                continue
            chemin = os.path.join(DOSSIER_BACKUPS, nom)
            if not os.path.isdir(chemin):
                continue
            if not _est_dossier_backup_valide(chemin, nom):
                continue
            sauvegardes.append(_backup_vers_dict(chemin))

        sauvegardes.sort(
            key=lambda s: (s["date"], s["heure"]),
            reverse=True,
        )
        return sauvegardes
    except OSError as erreur:
        raise RuntimeError("Echec de la lecture des sauvegardes.") from erreur


def get_derniere_sauvegarde() -> dict[str, Any] | None:
    """Retourne la sauvegarde la plus recente ou None."""
    liste = get_liste_backups()
    return liste[0] if liste else None


def clean_old_backups(nb_jours: int = 30, garder_minimum: int = 5) -> int:
    """Purge les dossiers de sauvegarde de plus de nb_jours (conserve au moins garder_minimum).

    Appelee par la tache hebdomadaire du scheduler, distincte de la sauvegarde
    quotidienne automatique (create_backup a minuit). Ne cree pas de copie.
    """
    liste = get_liste_backups()
    if len(liste) <= garder_minimum:
        return 0

    maintenant = datetime.now()
    liste_asc = sorted(liste, key=lambda s: (s["date"], s["heure"]))
    supprimees = 0

    try:
        for backup in liste_asc:
            if len(liste) - supprimees <= garder_minimum:
                break
            try:
                date_backup = datetime.strptime(backup["date"], "%Y-%m-%d")
            except ValueError:
                continue
            age_jours = (maintenant - date_backup).days
            if age_jours > nb_jours:
                shutil.rmtree(backup["chemin"])
                supprimees += 1

        if supprimees > 0:
            enregistrer_audit(
                None,
                "nettoyage_sauvegardes",
                f"{supprimees} sauvegarde(s) supprimee(s)",
                MODULE_SYSTEME,
            )
        return supprimees
    except (OSError, shutil.Error) as erreur:
        raise RuntimeError("Echec du nettoyage des sauvegardes.") from erreur


def supprimer_backup(chemin_backup: str, user_id: int | None = None) -> None:
    """Supprime un dossier de sauvegarde."""
    try:
        chemin_absolu = _est_sous_dossier_backups(chemin_backup)
        if _contient_pre_restore(chemin_absolu):
            raise RuntimeError(
                "La suppression des sauvegardes de securite est interdite."
            )
        if not os.path.isdir(chemin_absolu):
            raise RuntimeError("Sauvegarde introuvable.")
        nom = os.path.basename(chemin_absolu)
        shutil.rmtree(chemin_absolu)
        enregistrer_audit(
            user_id,
            "sauvegarde_supprimee",
            nom,
            MODULE_SYSTEME,
        )
    except (OSError, shutil.Error) as erreur:
        raise RuntimeError("Echec de la suppression de la sauvegarde.") from erreur


def restore_backup(chemin_backup: str, user_id: int | None = None) -> None:
    """Restaure une sauvegarde (necessite redemarrage si la DB est verrouillee)."""
    try:
        chemin_absolu = _est_sous_dossier_backups(chemin_backup)
        chemin_db_backup = os.path.join(chemin_absolu, "courriers.db")
        if not os.path.isfile(chemin_db_backup):
            raise RuntimeError(
                "Sauvegarde invalide : courriers.db introuvable."
            )

        create_backup(user_id, securite_pre_restore=True)

        try:
            shutil.copy2(chemin_db_backup, CHEMIN_DB)
        except PermissionError as erreur:
            raise RuntimeError(
                "Impossible de remplacer courriers.db : fichier verrouille. "
                "Fermez l'application et reessayez, ou redemarrez apres "
                "confirmation."
            ) from erreur

        chemin_uploads_backup = os.path.join(chemin_absolu, "uploads")
        if os.path.isdir(chemin_uploads_backup):
            if os.path.isdir(DOSSIER_UPLOADS):
                shutil.rmtree(DOSSIER_UPLOADS)
            shutil.copytree(chemin_uploads_backup, DOSSIER_UPLOADS)
        else:
            if os.path.isdir(DOSSIER_UPLOADS):
                shutil.rmtree(DOSSIER_UPLOADS)
            creer_dossier_uploads()

        chemin_exports_backup = os.path.join(chemin_absolu, "exports")
        if os.path.isdir(chemin_exports_backup):
            if os.path.isdir(DOSSIER_EXPORTS):
                shutil.rmtree(DOSSIER_EXPORTS)
            shutil.copytree(chemin_exports_backup, DOSSIER_EXPORTS)
        else:
            if os.path.isdir(DOSSIER_EXPORTS):
                shutil.rmtree(DOSSIER_EXPORTS)
            creer_dossier_exports()

        enregistrer_audit(
            user_id,
            "sauvegarde_restauree",
            os.path.basename(chemin_absolu),
            MODULE_SYSTEME,
        )
    except RuntimeError:
        raise
    except (OSError, shutil.Error) as erreur:
        raise RuntimeError("Echec de la restauration de la sauvegarde.") from erreur
