# -*- coding: utf-8 -*-
"""Service de gestion des utilisateurs (administration)."""

import sqlite3
from typing import Any

from database import models
from database.db import get_connection
from services.auth import generer_mot_de_passe_temporaire, hasher_mot_de_passe
from utils.audit import enregistrer_audit
from utils.constants import ROLES_VALIDES

MODULE_USERS = "users"


def _sans_mot_de_passe(utilisateur: dict[str, Any]) -> dict[str, Any]:
    return {cle: valeur for cle, valeur in utilisateur.items() if cle != "mot_de_passe"}


def _valider_champs_obligatoires(data: dict[str, Any]) -> None:
    for cle in ("prenom", "nom", "email", "role"):
        if not str(data.get(cle, "")).strip():
            raise ValueError(f"Le champ {cle} est obligatoire.")
    if data["role"] not in ROLES_VALIDES:
        raise ValueError("R\u00f4le invalide.")


def _verifier_garde_fous_admin(
    connexion: sqlite3.Connection,
    cible_id: int,
    admin_id: int,
    *,
    nouveau_role: str | None = None,
    desactivation: bool = False,
) -> None:
    """Emp\u00eache la suppression du dernier admin ou l'auto-d\u00e9sactivation."""
    cible = models.obtenir_utilisateur_admin_par_id(connexion, cible_id)
    if cible is None:
        raise ValueError("Utilisateur introuvable.")

    if desactivation and cible_id == admin_id:
        raise ValueError("Vous ne pouvez pas vous d\u00e9sactiver vous-m\u00eame.")

    role_final = nouveau_role if nouveau_role is not None else cible["role"]
    retire_admin = cible["role"] == "admin" and role_final != "admin"
    devient_inactif = desactivation or (
        nouveau_role is None and int(cible.get("actif", 1)) == 0
    )

    if cible_id == admin_id and nouveau_role is not None and nouveau_role != "admin":
        raise ValueError("Vous ne pouvez pas retirer votre propre r\u00f4le admin.")

    if cible["role"] == "admin" and int(cible.get("actif", 1)) == 1:
        if desactivation or retire_admin:
            if models.compter_admins_actifs(connexion) <= 1:
                raise ValueError(
                    "Impossible de d\u00e9sactiver ou modifier le dernier "
                    "administrateur actif."
                )


def lister_utilisateurs(
    recherche: str | None = None,
    role: str | None = None,
) -> list[dict[str, Any]]:
    """Liste les utilisateurs sans exposer les mots de passe."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        utilisateurs = models.obtenir_tous_utilisateurs(connexion, recherche, role)
        return [_sans_mot_de_passe(dict(u)) for u in utilisateurs]
    except sqlite3.Error as erreur:
        raise RuntimeError("Echec de la liste des utilisateurs.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def creer_utilisateur_admin(data: dict[str, Any], admin_id: int) -> int:
    """Cr\u00e9e un utilisateur avec mot de passe hash\u00e9."""
    _valider_champs_obligatoires(data)
    mot_de_passe = str(data.get("mot_de_passe", "")).strip()
    if not mot_de_passe:
        raise ValueError("Le mot de passe est obligatoire.")

    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        email = str(data["email"]).strip()
        if models.email_utilisateur_existe(connexion, email):
            raise ValueError("Cet email est d\u00e9j\u00e0 utilis\u00e9.")

        user_id = models.creer_utilisateur(
            connexion,
            {
                "prenom": str(data["prenom"]).strip(),
                "nom": str(data["nom"]).strip(),
                "email": email,
                "role": data["role"],
                "mot_de_passe_hash": hasher_mot_de_passe(mot_de_passe),
                "actif": int(data.get("actif", 1)),
            },
        )
        connexion.commit()
        enregistrer_audit(
            admin_id,
            "creation_utilisateur",
            f"Creation utilisateur {email} (id {user_id})",
            MODULE_USERS,
        )
        return user_id
    except sqlite3.Error as erreur:
        raise RuntimeError("Echec de la creation de l'utilisateur.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def mettre_a_jour_utilisateur_admin(
    user_id: int, data: dict[str, Any], admin_id: int
) -> None:
    """Met \u00e0 jour un utilisateur existant."""
    _valider_champs_obligatoires(data)

    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        email = str(data["email"]).strip()
        if models.email_utilisateur_existe(connexion, email, exclure_id=user_id):
            raise ValueError("Cet email est d\u00e9j\u00e0 utilis\u00e9.")

        _verifier_garde_fous_admin(
            connexion,
            user_id,
            admin_id,
            nouveau_role=data["role"],
        )

        actif = int(data.get("actif", 1))
        if actif == 0:
            _verifier_garde_fous_admin(
                connexion, user_id, admin_id, desactivation=True
            )

        models.mettre_a_jour_utilisateur(
            connexion,
            user_id,
            {
                "prenom": str(data["prenom"]).strip(),
                "nom": str(data["nom"]).strip(),
                "email": email,
                "role": data["role"],
                "actif": actif,
            },
        )
        connexion.commit()
        enregistrer_audit(
            admin_id,
            "modification_utilisateur",
            f"Modification utilisateur {email} (id {user_id})",
            MODULE_USERS,
        )
    except sqlite3.Error as erreur:
        raise RuntimeError("Echec de la mise a jour de l'utilisateur.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def basculer_actif_utilisateur_admin(user_id: int, admin_id: int) -> bool:
    """Inverse le statut actif et retourne le nouvel \u00e9tat."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        cible = models.obtenir_utilisateur_admin_par_id(connexion, user_id)
        if cible is None:
            raise ValueError("Utilisateur introuvable.")

        actuel = int(cible.get("actif", 1))
        nouveau = 0 if actuel == 1 else 1

        if nouveau == 0:
            _verifier_garde_fous_admin(
                connexion, user_id, admin_id, desactivation=True
            )

        models.basculer_actif_utilisateur(connexion, user_id, nouveau)
        connexion.commit()

        action = (
            "activation_utilisateur"
            if nouveau == 1
            else "desactivation_utilisateur"
        )
        enregistrer_audit(
            admin_id,
            action,
            f"{action.replace('_', ' ')} {cible['email']} (id {user_id})",
            MODULE_USERS,
        )
        return bool(nouveau)
    except sqlite3.Error as erreur:
        raise RuntimeError("Echec du changement de statut.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def reinitialiser_mot_de_passe_admin(
    user_id: int, admin_id: int, mot_de_passe: str | None = None
) -> str:
    """R\u00e9initialise le mot de passe et retourne le mot de passe en clair."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        cible = models.obtenir_utilisateur_admin_par_id(connexion, user_id)
        if cible is None:
            raise ValueError("Utilisateur introuvable.")

        mdp = mot_de_passe or generer_mot_de_passe_temporaire()
        models.reinitialiser_mot_de_passe_utilisateur(
            connexion, user_id, hasher_mot_de_passe(mdp)
        )
        connexion.commit()
        enregistrer_audit(
            admin_id,
            "reinitialisation_mot_de_passe",
            f"Reinitialisation mot de passe pour {cible['email']} (id {user_id})",
            MODULE_USERS,
        )
        return mdp
    except sqlite3.Error as erreur:
        raise RuntimeError("Echec de la reinitialisation du mot de passe.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def obtenir_journal_audit(
    limit: int = 20, module: str | None = None
) -> list[dict[str, Any]]:
    """Retourne les derni\u00e8res entr\u00e9es du journal d'audit."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        return models.obtenir_journal_audit(connexion, limit, module)
    except sqlite3.Error as erreur:
        raise RuntimeError("Echec de la recuperation du journal.") from erreur
    finally:
        if connexion is not None:
            connexion.close()
