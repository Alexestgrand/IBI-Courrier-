# -*- coding: utf-8 -*-
"""Vue de gestion des sauvegardes et restaurations."""

import os
from typing import Any

import customtkinter as ctk

from utils.backup import (
    chemin_dossier_backups,
    create_backup,
    get_derniere_sauvegarde,
    get_liste_backups,
    restore_backup,
    supprimer_backup,
)
from utils.scheduler import (
    get_backup_auto_actif,
    get_nettoyage_auto_actif,
    get_prochaine_sauvegarde,
    set_backup_auto_actif,
    set_nettoyage_auto_actif,
)
from utils.theme import (
    ACCENT,
    ACCENT_HOVER,
    DANGER,
    ERREUR,
    FOND_CONTENU,
    HAUTEUR_BOUTON_LIGNE,
    POLICE_PETIT,
    POLICE_SOUS_TITRE,
    POLICE_TEXTE,
    SECONDAIRE,
    SUCCES,
    TEXTE_PRIMAIRE,
    TEXTE_SECONDAIRE,
)
from views.ui_helpers import (
    afficher_modale_confirmation,
    afficher_modale_message,
    alterner_couleur_ligne,
    configurer_grille_tableau,
    creer_barre_titre,
    creer_entete_tableau,
    creer_etat_vide,
)

LARGEURS_COLONNES = (100, 80, 90, 80, 200)
COLONNES_SAUVEGARDES = ("Date", "Heure", "Taille", "Nb fichiers", "Actions")


def _formater_taille(octets: int) -> str:
    if octets >= 1024 * 1024:
        return f"{octets / (1024 * 1024):.1f} Mo"
    if octets >= 1024:
        return f"{octets / 1024:.1f} Ko"
    return f"{octets} o"


class SauvegardesView(ctk.CTkFrame):
    """Sauvegardes manuelles, restauration et parametres."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        *,
        utilisateur: dict[str, Any],
        couleur_contenu: str = FOND_CONTENU,
    ) -> None:
        super().__init__(parent, fg_color=couleur_contenu, corner_radius=0)
        self.utilisateur = utilisateur
        self.couleur_contenu = couleur_contenu
        self.pack(fill="both", expand=True)

        if utilisateur.get("role") not in ("admin", "dg"):
            ctk.CTkLabel(
                self,
                text=(
                    "Acc\u00e8s r\u00e9serv\u00e9 aux administrateurs "
                    "et \u00e0 la direction"
                ),
                font=POLICE_SOUS_TITRE,
                text_color=ERREUR,
            ).pack(pady=48, padx=32)
            return

        self._construire_interface()
        self.charger_liste()
        self._mettre_a_jour_infos()

    def _construire_interface(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True)

        creer_barre_titre(scroll, "Sauvegardes & Restauration")

        section_manuelle = ctk.CTkFrame(scroll, fg_color="transparent")
        section_manuelle.pack(fill="x", padx=24, pady=(0, 12))

        ctk.CTkButton(
            section_manuelle,
            text="Cr\u00e9er une sauvegarde maintenant",
            font=POLICE_TEXTE,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._creer_sauvegarde_manuelle,
        ).pack(anchor="w", pady=(0, 8))

        self.label_derniere = ctk.CTkLabel(
            section_manuelle,
            text="Derni\u00e8re sauvegarde : \u2014",
            font=POLICE_TEXTE,
            text_color=TEXTE_SECONDAIRE,
            anchor="w",
        )
        self.label_derniere.pack(fill="x", pady=2)

        self.label_prochaine = ctk.CTkLabel(
            section_manuelle,
            text="Prochaine sauvegarde automatique : \u2014",
            font=POLICE_TEXTE,
            text_color=TEXTE_SECONDAIRE,
            anchor="w",
        )
        self.label_prochaine.pack(fill="x", pady=2)

        ctk.CTkLabel(
            section_manuelle,
            text=(
                "Sauvegarde automatique : quotidienne \u00e0 minuit.\n"
                "La t\u00e2che hebdomadaire supprime les copies de plus de 30 jours "
                "(ce n'est pas une sauvegarde suppl\u00e9mentaire)."
            ),
            font=POLICE_PETIT,
            text_color=TEXTE_SECONDAIRE,
            anchor="w",
            justify="left",
            wraplength=720,
        ).pack(fill="x", pady=(4, 0))

        ctk.CTkLabel(
            scroll,
            text="Sauvegardes disponibles",
            font=POLICE_SOUS_TITRE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        ).pack(fill="x", padx=24, pady=(12, 4))

        creer_entete_tableau(scroll, list(COLONNES_SAUVEGARDES), LARGEURS_COLONNES)

        self.zone_liste = ctk.CTkScrollableFrame(
            scroll, fg_color="transparent", corner_radius=0, height=300
        )
        self.zone_liste.pack(fill="x", padx=24, pady=(0, 16))

        section_params = ctk.CTkFrame(scroll, fg_color="transparent")
        section_params.pack(fill="x", padx=24, pady=(8, 24))

        ctk.CTkLabel(
            section_params,
            text="Param\u00e8tres",
            font=POLICE_SOUS_TITRE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        self.switch_backup_auto = ctk.CTkSwitch(
            section_params,
            text="Sauvegarde quotidienne automatique",
            font=POLICE_TEXTE,
            command=self._toggle_backup_auto,
        )
        if get_backup_auto_actif():
            self.switch_backup_auto.select()
        self.switch_backup_auto.pack(anchor="w", pady=4)

        self.switch_nettoyage = ctk.CTkSwitch(
            section_params,
            text="Purge des anciennes sauvegardes (> 30 jours, min. 5 conserv\u00e9es)",
            font=POLICE_TEXTE,
            command=self._toggle_nettoyage_auto,
        )
        if get_nettoyage_auto_actif():
            self.switch_nettoyage.select()
        self.switch_nettoyage.pack(anchor="w", pady=4)

        ctk.CTkButton(
            section_params,
            text="Ouvrir le dossier des sauvegardes",
            font=POLICE_TEXTE,
            fg_color=SECONDAIRE,
            command=self._ouvrir_dossier_backups,
        ).pack(anchor="w", pady=(12, 0))

    def _mettre_a_jour_infos(self) -> None:
        derniere = get_derniere_sauvegarde()
        if derniere:
            date_aff = derniere["date"].replace("-", "/")
            self.label_derniere.configure(
                text=(
                    f"Derni\u00e8re sauvegarde : {date_aff} "
                    f"{derniere['heure']}, "
                    f"{_formater_taille(derniere['taille_octets'])}"
                )
            )
        else:
            self.label_derniere.configure(
                text="Derni\u00e8re sauvegarde : \u2014"
            )

        prochaine = get_prochaine_sauvegarde()
        if prochaine and get_backup_auto_actif():
            self.label_prochaine.configure(
                text=(
                    f"Prochaine sauvegarde automatique : "
                    f"{prochaine.strftime('%d/%m/%Y')} \u00e0 00:00"
                )
            )
        else:
            self.label_prochaine.configure(
                text="Prochaine sauvegarde automatique : d\u00e9sactiv\u00e9e"
            )

    def _toggle_backup_auto(self) -> None:
        actif = bool(self.switch_backup_auto.get())
        set_backup_auto_actif(actif)
        self._mettre_a_jour_infos()

    def _toggle_nettoyage_auto(self) -> None:
        set_nettoyage_auto_actif(bool(self.switch_nettoyage.get()))

    def _ouvrir_dossier_backups(self) -> None:
        try:
            os.startfile(chemin_dossier_backups())  # noqa: S606
        except OSError:
            afficher_modale_message(
                self,
                "Erreur",
                "Impossible d'ouvrir le dossier des sauvegardes.",
                couleur=ERREUR,
            )

    def _creer_sauvegarde_manuelle(self) -> None:
        try:
            chemin = create_backup(user_id=self.utilisateur["id"])
            nom = os.path.basename(chemin)
            afficher_modale_message(
                self,
                "Sauvegarde cr\u00e9\u00e9e",
                f"La sauvegarde a \u00e9t\u00e9 cr\u00e9\u00e9e avec succ\u00e8s.\n\nDossier : {nom}",
                couleur=SUCCES,
            )
            self.charger_liste()
            self._mettre_a_jour_infos()
        except RuntimeError as erreur:
            afficher_modale_message(self, "Erreur", str(erreur), couleur=ERREUR)

    def charger_liste(self) -> None:
        """Recharge la liste des sauvegardes."""
        if not hasattr(self, "zone_liste"):
            return

        for widget in self.zone_liste.winfo_children():
            widget.destroy()

        try:
            sauvegardes = get_liste_backups()
        except RuntimeError:
            ctk.CTkLabel(
                self.zone_liste,
                text="Erreur lors du chargement.",
                font=POLICE_TEXTE,
                text_color=ERREUR,
            ).pack(pady=12)
            return

        if not sauvegardes:
            creer_etat_vide(
                self.zone_liste,
                "Aucune sauvegarde disponible",
                sous_message="Cr\u00e9ez une sauvegarde manuelle pour commencer.",
            )
            return

        for index, backup in enumerate(sauvegardes):
            self._ajouter_ligne_backup(backup, index)

    def _ajouter_ligne_backup(
        self, backup: dict[str, Any], index: int
    ) -> None:
        couleur_base = alterner_couleur_ligne(index)
        ligne = ctk.CTkFrame(
            self.zone_liste, fg_color=couleur_base, corner_radius=4
        )
        ligne.pack(fill="x", pady=2)
        configurer_grille_tableau(ligne, LARGEURS_COLONNES, colonne_extensible=4)

        date_aff = backup["date"].replace("-", "/")
        ctk.CTkLabel(
            ligne,
            text=date_aff,
            font=POLICE_TEXTE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        ).grid(row=0, column=0, padx=6, pady=6, sticky="ew")

        ctk.CTkLabel(
            ligne,
            text=backup.get("heure", ""),
            font=POLICE_TEXTE,
            text_color=TEXTE_SECONDAIRE,
            anchor="w",
        ).grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        ctk.CTkLabel(
            ligne,
            text=_formater_taille(int(backup.get("taille_octets", 0))),
            font=POLICE_TEXTE,
            text_color=TEXTE_SECONDAIRE,
            anchor="w",
        ).grid(row=0, column=2, padx=6, pady=6, sticky="ew")

        ctk.CTkLabel(
            ligne,
            text=str(backup.get("nb_fichiers", 0)),
            font=POLICE_TEXTE,
            text_color=TEXTE_SECONDAIRE,
            anchor="w",
        ).grid(row=0, column=3, padx=6, pady=6, sticky="ew")

        actions = ctk.CTkFrame(ligne, fg_color="transparent")
        actions.grid(row=0, column=4, padx=4, pady=4, sticky="ew")

        chemin = backup["chemin"]
        ctk.CTkButton(
            actions,
            text="Restaurer",
            width=80,
            height=HAUTEUR_BOUTON_LIGNE,
            font=POLICE_PETIT,
            fg_color=DANGER,
            command=lambda c=chemin: self._confirmer_restauration(c),
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            actions,
            text="Supprimer",
            width=80,
            height=HAUTEUR_BOUTON_LIGNE,
            font=POLICE_PETIT,
            fg_color=SECONDAIRE,
            command=lambda c=chemin: self._confirmer_suppression(c),
        ).pack(side="left", padx=2)

    def _confirmer_restauration(self, chemin_backup: str) -> None:
        message = (
            "\u26a0\ufe0f Cette action remplacera toutes les donn\u00e9es actuelles.\n"
            "Un backup de s\u00e9curit\u00e9 sera cr\u00e9\u00e9 automatiquement.\n"
            "Confirmer ?"
        )

        def confirmer() -> None:
            restore_backup(chemin_backup, self.utilisateur["id"])
            afficher_modale_message(
                self,
                "Restauration effectu\u00e9e",
                (
                    "La restauration a \u00e9t\u00e9 lanc\u00e9e.\n\n"
                    "Red\u00e9marrez l'application pour finaliser "
                    "la restauration."
                ),
                couleur=SUCCES,
            )
            self.charger_liste()
            self._mettre_a_jour_infos()

        afficher_modale_confirmation(
            self,
            "Confirmer la restauration",
            message,
            confirmer_label="Confirmer",
            on_confirmer=confirmer,
        )

    def _confirmer_suppression(self, chemin_backup: str) -> None:
        def confirmer() -> None:
            supprimer_backup(chemin_backup, self.utilisateur["id"])
            self.charger_liste()
            self._mettre_a_jour_infos()

        afficher_modale_confirmation(
            self,
            "Confirmer la suppression",
            "Supprimer d\u00e9finitivement cette sauvegarde ?",
            confirmer_label="Supprimer",
            on_confirmer=confirmer,
        )
