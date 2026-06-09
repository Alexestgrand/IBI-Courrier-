"""Service d'authentification."""

import secrets
import sqlite3
import string
from typing import Any

import bcrypt

from database import models
from database.db import get_connection
from utils.audit import enregistrer_audit

MODULE_AUTH = "auth"


def generer_mot_de_passe_temporaire() -> str:
    """Génère un mot de passe temporaire de 10 caractères."""
    minuscules = string.ascii_lowercase
    majuscules = string.ascii_uppercase
    chiffres = string.digits
    symboles = "!@#$%&*"
    caracteres = [
        secrets.choice(majuscules),
        secrets.choice(minuscules),
        secrets.choice(chiffres),
        secrets.choice(symboles),
    ]
    pool = minuscules + majuscules + chiffres + symboles
    caracteres.extend(secrets.choice(pool) for _ in range(6))
    secrets.SystemRandom().shuffle(caracteres)
    return "".join(caracteres)


def hasher_mot_de_passe(mot_de_passe: str) -> str:
    """Retourne le hash bcrypt d'un mot de passe."""
    return bcrypt.hashpw(mot_de_passe.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verifier_mot_de_passe(mot_de_passe: str, mot_de_passe_hash: str) -> bool:
    """Vérifie un mot de passe contre son hash."""
    return bcrypt.checkpw(
        mot_de_passe.encode("utf-8"),
        mot_de_passe_hash.encode("utf-8"),
    )


def _sans_mot_de_passe(utilisateur: dict[str, Any]) -> dict[str, Any]:
    """Retire le mot de passe d'un dictionnaire utilisateur."""
    return {cle: valeur for cle, valeur in utilisateur.items() if cle != "mot_de_passe"}


def obtenir_utilisateur_par_id(user_id: int) -> dict[str, Any] | None:
    """Retourne un utilisateur actif sans le mot de passe, ou None."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        utilisateur = models.obtenir_utilisateur_par_id(connexion, user_id)
        if utilisateur is None:
            return None
        return _sans_mot_de_passe(dict(utilisateur))
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la récupération de l'utilisateur.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def authentifier(email: str, mot_de_passe: str) -> dict[str, Any] | None:
    """Vérifie les identifiants et retourne l'utilisateur, ou None si invalide."""
    email_normalise = email.strip()
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        utilisateur = models.obtenir_utilisateur_par_email(connexion, email_normalise)

        if utilisateur is None:
            enregistrer_audit(
                None,
                "connexion_echouee",
                f"Tentative de connexion pour {email_normalise}",
                MODULE_AUTH,
            )
            return None

        utilisateur_dict = dict(utilisateur)
        if not verifier_mot_de_passe(mot_de_passe, utilisateur_dict["mot_de_passe"]):
            enregistrer_audit(
                utilisateur_dict["id"],
                "connexion_echouee",
                f"Mot de passe incorrect pour {email_normalise}",
                MODULE_AUTH,
            )
            return None

        utilisateur_safe = _sans_mot_de_passe(utilisateur_dict)
        models.mettre_a_jour_derniere_connexion(connexion, utilisateur_dict["id"])
        connexion.commit()
        enregistrer_audit(
            utilisateur_safe["id"],
            "connexion_reussie",
            f"Connexion réussie pour {email_normalise}",
            MODULE_AUTH,
        )
        return utilisateur_safe
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de l'authentification.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def login(email: str, mot_de_passe: str) -> dict[str, Any] | None:
    """Alias de authentifier."""
    return authentifier(email, mot_de_passe)
