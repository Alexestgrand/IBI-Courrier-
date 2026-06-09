"""Service métier des courriers."""

import os
import sqlite3
from typing import Any

from database import models
from database.db import get_connection
from utils.audit import enregistrer_audit
from utils.constants import TRANSITIONS_PAR_ROLE, TRANSITIONS_VALIDES
from utils.export_pdf import generer_courrier_sortant
from utils.exports import ouvrir_fichier_export
from utils.fichiers import copier_piece_jointe

MODULE_COURRIERS = "courriers"


def _transition_autorisee(role: str, ancien: str, nouveau: str) -> bool:
    """Vérifie si un rôle peut effectuer une transition de statut."""
    regles = TRANSITIONS_PAR_ROLE.get(role, ())
    if regles == "toutes":
        return nouveau in TRANSITIONS_VALIDES.get(ancien, ())
    if not isinstance(regles, tuple):
        return False
    return (ancien, nouveau) in regles


def obtenir_statuts_possibles(role: str, statut_actuel: str) -> list[str]:
    """Retourne les statuts cibles autorisés pour un rôle et un statut courant."""
    regles = TRANSITIONS_PAR_ROLE.get(role, ())
    if regles == "toutes":
        return list(TRANSITIONS_VALIDES.get(statut_actuel, ()))
    if not isinstance(regles, tuple) or not regles:
        return []
    return [
        nouveau
        for ancien, nouveau in regles
        if ancien == statut_actuel
    ]


def lister_courriers_entrants(
    filtre_statut: str | None = None,
    recherche: str | None = None,
) -> list[dict[str, Any]]:
    """Liste les courriers entrants."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        return models.obtenir_courriers_entrants(
            connexion, filtre_statut, recherche
        )
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec du listage des courriers.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def obtenir_courrier(courrier_id: int) -> dict[str, Any] | None:
    """Retourne un courrier par identifiant."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        return models.obtenir_courrier_par_id(connexion, courrier_id)
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la récupération du courrier.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def generer_numero_entrant() -> str:
    """Génère le prochain numéro de courrier entrant."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        return models.obtenir_numero_auto(connexion, "entrant")
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la génération du numéro.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def lister_services() -> list[str]:
    """Retourne les noms des services actifs."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        services = models.obtenir_services_actifs(connexion)
        return [s["nom"] for s in services]
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la récupération des services.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def obtenir_historique(courrier_id: int) -> list[dict[str, Any]]:
    """Retourne l'historique des statuts d'un courrier."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        return models.obtenir_historique_statuts(connexion, courrier_id)
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la récupération de l'historique.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def creer_courrier_entrant(data: dict[str, Any], user_id: int) -> int:
    """Crée un courrier entrant avec journalisation."""
    champs_obligatoires = ("expediteur", "objet", "service_destinataire")
    for champ in champs_obligatoires:
        if not data.get(champ) or not str(data[champ]).strip():
            raise ValueError(f"Le champ « {champ} » est obligatoire.")

    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        numero = data.get("numero") or models.obtenir_numero_auto(
            connexion, "entrant"
        )

        fichier_joint = data.get("fichier_joint")
        chemin_source = data.get("chemin_piece_jointe_source")
        if chemin_source:
            fichier_joint = copier_piece_jointe(chemin_source, numero)

        payload = {
            "numero": numero,
            "type": "entrant",
            "date_reception": data.get("date_reception"),
            "expediteur": data["expediteur"].strip(),
            "reference_document": data.get("reference_document"),
            "objet": data["objet"].strip(),
            "service_destinataire": data["service_destinataire"].strip(),
            "urgence": data.get("urgence", "normal"),
            "statut": "en_attente",
            "observations": data.get("observations"),
            "fichier_joint": fichier_joint,
            "created_by": user_id,
        }

        courrier_id = models.creer_courrier(connexion, payload)
        models.inserer_log_statut(
            connexion,
            courrier_id,
            None,
            "en_attente",
            user_id,
            "Création",
        )
        connexion.commit()

        enregistrer_audit(
            user_id,
            "creation_courrier",
            f"Courrier {numero}",
            MODULE_COURRIERS,
        )
        return courrier_id
    except sqlite3.Error as erreur:
        if connexion is not None:
            connexion.rollback()
        raise RuntimeError("Échec de la création du courrier.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def changer_statut(
    courrier_id: int,
    nouveau_statut: str,
    user_id: int,
    observation: str | None,
    role_utilisateur: str,
) -> None:
    """Change le statut d'un courrier si la transition est autorisée."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        courrier = models.obtenir_courrier_par_id(connexion, courrier_id)
        if courrier is None:
            raise ValueError("Courrier introuvable.")

        ancien_statut = courrier["statut"]
        if not _transition_autorisee(role_utilisateur, ancien_statut, nouveau_statut):
            raise ValueError(
                f"Transition non autorisée : {ancien_statut} → {nouveau_statut} "
                f"pour le rôle « {role_utilisateur} »."
            )

        models.mettre_a_jour_statut(
            connexion, courrier_id, nouveau_statut, user_id, observation
        )
        connexion.commit()

        enregistrer_audit(
            user_id,
            "changement_statut",
            f"{courrier['numero']} : {ancien_statut} → {nouveau_statut}",
            MODULE_COURRIERS,
        )
    except sqlite3.Error as erreur:
        if connexion is not None:
            connexion.rollback()
        raise RuntimeError("Échec du changement de statut.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def lister_courriers_sortants(
    filtre_statut: str | None = None,
    recherche: str | None = None,
) -> list[dict[str, Any]]:
    """Liste les courriers sortants."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        return models.obtenir_courriers_sortants(
            connexion, filtre_statut, recherche
        )
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec du listage des courriers sortants.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def generer_numero_sortant() -> str:
    """Prévisualise le prochain numéro sortant (indicatif UI uniquement)."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        return models.obtenir_numero_auto(connexion, "sortant")
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la génération du numéro.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def creer_courrier_sortant(data: dict[str, Any], user_id: int) -> tuple[int, str]:
    """Crée un courrier sortant, génère le PDF et journalise."""
    champs_obligatoires = (
        "destinataire",
        "objet",
        "service_emetteur",
        "corps_courrier",
    )
    for champ in champs_obligatoires:
        if not data.get(champ) or not str(data[champ]).strip():
            raise ValueError(f"Le champ « {champ} » est obligatoire.")

    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        numero = models.obtenir_numero_auto(connexion, "sortant")

        fichier_joint = data.get("fichier_joint")
        chemin_source = data.get("chemin_piece_jointe_source")
        if chemin_source:
            fichier_joint = copier_piece_jointe(chemin_source, numero)

        payload = {
            "numero": numero,
            "date_reception": data.get("date_reception"),
            "destinataire": data["destinataire"].strip(),
            "adresse_destinataire": data.get("adresse_destinataire"),
            "objet": data["objet"].strip(),
            "service_emetteur": data["service_emetteur"].strip(),
            "urgence": data.get("urgence", "normal"),
            "corps_courrier": data["corps_courrier"].strip(),
            "observations": data.get("observations"),
            "fichier_joint": fichier_joint,
            "created_by": user_id,
        }

        courrier_id = models.creer_courrier_sortant(connexion, payload)
        models.inserer_log_statut(
            connexion,
            courrier_id,
            None,
            "en_attente",
            user_id,
            "Création",
        )

        courrier_complet = models.obtenir_courrier_par_id(connexion, courrier_id)
        if courrier_complet is None:
            raise RuntimeError("Courrier introuvable après création.")

        chemin_pdf = generer_courrier_sortant(dict(courrier_complet))
        models.mettre_a_jour_chemin_pdf(connexion, courrier_id, chemin_pdf)
        connexion.commit()

        enregistrer_audit(
            user_id,
            "creation_courrier_sortant",
            f"Courrier {numero}",
            MODULE_COURRIERS,
        )
        return courrier_id, chemin_pdf
    except sqlite3.Error as erreur:
        if connexion is not None:
            connexion.rollback()
        raise RuntimeError("Échec de la création du courrier sortant.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def ouvrir_pdf_sortant(courrier_id: int, user_id: int | None = None) -> None:
    """Ouvre le PDF d'un courrier sortant, régénère si nécessaire."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        courrier = models.obtenir_courrier_par_id(connexion, courrier_id)
        if courrier is None:
            raise ValueError("Courrier introuvable.")

        courrier_dict = dict(courrier)
        chemin_pdf = courrier_dict.get("chemin_pdf")
        regeneration = False

        if chemin_pdf:
            from utils.exports import chemin_absolu_export

            if not os.path.isfile(chemin_absolu_export(chemin_pdf)):
                regeneration = True
        else:
            regeneration = True

        if regeneration:
            chemin_pdf = generer_courrier_sortant(courrier_dict)
            models.mettre_a_jour_chemin_pdf(connexion, courrier_id, chemin_pdf)
            connexion.commit()
            if user_id is not None:
                enregistrer_audit(
                    user_id,
                    "regeneration_pdf_sortant",
                    f"Courrier {courrier_dict.get('numero', '')}",
                    MODULE_COURRIERS,
                )
        elif user_id is not None:
            enregistrer_audit(
                user_id,
                "ouverture_pdf_sortant",
                f"Courrier {courrier_dict.get('numero', '')}",
                MODULE_COURRIERS,
            )

        ouvrir_fichier_export(chemin_pdf)
    except sqlite3.Error as erreur:
        if connexion is not None:
            connexion.rollback()
        raise RuntimeError("Échec de l'ouverture du PDF sortant.") from erreur
    finally:
        if connexion is not None:
            connexion.close()


def regenerer_pdf_sortant(courrier_id: int, user_id: int) -> str:
    """Régénère le PDF d'un courrier sortant."""
    connexion: sqlite3.Connection | None = None
    try:
        connexion = get_connection()
        courrier = models.obtenir_courrier_par_id(connexion, courrier_id)
        if courrier is None:
            raise ValueError("Courrier introuvable.")

        chemin_pdf = generer_courrier_sortant(dict(courrier))
        models.mettre_a_jour_chemin_pdf(connexion, courrier_id, chemin_pdf)
        connexion.commit()

        enregistrer_audit(
            user_id,
            "regeneration_pdf_sortant",
            f"Courrier {courrier['numero']}",
            MODULE_COURRIERS,
        )
        return chemin_pdf
    except sqlite3.Error as erreur:
        if connexion is not None:
            connexion.rollback()
        raise RuntimeError("Échec de la régénération du PDF.") from erreur
    finally:
        if connexion is not None:
            connexion.close()
