# -*- coding: utf-8 -*-
"""Vue de recherche avancee multi-criteres."""

import tkinter.filedialog as filedialog
from typing import Any

import customtkinter as ctk

from services.courriers import lister_services
from services.recherche import exporter_rapport_recherche, rechercher_courriers
from utils.constants import (
    COULEURS_STATUT,
    COULEURS_TYPE,
    COULEURS_URGENCE,
    FILTRES_STATUT_RECHERCHE,
    FILTRES_TYPE_RECHERCHE,
    FILTRES_URGENCE_RECHERCHE,
    LIBELLES_STATUT,
    LIBELLES_TYPE,
    LIBELLES_URGENCE,
)
from utils.theme import (
    ACCENT,
    ACCENT_HOVER,
    ERREUR,
    FOND_CONTENU,
    FOND_CARTE,
    POLICE_SOUS_TITRE,
    POLICE_TEXTE,
    RAYON_CARTE,
    SECONDAIRE,
    TEXTE_PRIMAIRE,
    TEXTE_SECONDAIRE,
)
from views.fiche_courrier import ouvrir_fiche_courrier
from views.ui_helpers import (
    alterner_couleur_ligne,
    configurer_grille_tableau,
    configurer_survol_ligne,
    creer_date_filtre,
    creer_entete_tableau,
    creer_etat_vide,
    lier_infobulle,
    lire_date_entry,
    reinitialiser_date_entry,
    tronquer_texte,
)

LARGEURS_COLONNES = (90, 70, 85, 120, 150, 100, 75, 80, 70)
COLONNES_TABLEAU = (
    "N\u00b0",
    "Type",
    "Date",
    "Contact",
    "Objet",
    "Service",
    "Urgence",
    "Statut",
    "Actions",
)


class RechercheView(ctk.CTkFrame):
    """Recherche avancee sur tous les courriers."""

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
        self.resultats: list[dict[str, Any]] = []
        self.filtres_appliques: dict[str, Any] = {}
        self.pack(fill="both", expand=True)
        self._construire_interface()

    def _construire_interface(self) -> None:
        section_filtres = ctk.CTkFrame(
            self, fg_color=FOND_CARTE, corner_radius=RAYON_CARTE
        )
        section_filtres.pack(fill="x", padx=24, pady=(16, 12))

        ctk.CTkLabel(
            section_filtres,
            text="Recherche avanc\u00e9e",
            font=POLICE_SOUS_TITRE,
            text_color=TEXTE_PRIMAIRE,
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=16, pady=(16, 12))

        self.champ_mot_cle = ctk.CTkEntry(
            section_filtres,
            placeholder_text="N\u00b0, objet, exp\u00e9diteur, destinataire\u2026",
            font=POLICE_TEXTE,
            width=280,
        )
        self.menu_type = ctk.CTkOptionMenu(
            section_filtres,
            values=list(FILTRES_TYPE_RECHERCHE.keys()),
            font=POLICE_TEXTE,
        )
        self.menu_type.set("Tous")
        self.menu_statut = ctk.CTkOptionMenu(
            section_filtres,
            values=list(FILTRES_STATUT_RECHERCHE.keys()),
            font=POLICE_TEXTE,
        )
        self.menu_statut.set("Tous")

        services = ["Tous"] + lister_services()
        self.menu_service = ctk.CTkOptionMenu(
            section_filtres, values=services, font=POLICE_TEXTE
        )
        self.menu_service.set("Tous")
        self.menu_urgence = ctk.CTkOptionMenu(
            section_filtres,
            values=list(FILTRES_URGENCE_RECHERCHE.keys()),
            font=POLICE_TEXTE,
        )
        self.menu_urgence.set("Tous")
        cadre_debut, self.champ_date_debut = creer_date_filtre(section_filtres)
        cadre_fin, self.champ_date_fin = creer_date_filtre(section_filtres)

        champs_l1 = (
            ("Mot-cl\u00e9", self.champ_mot_cle),
            ("Type", self.menu_type),
            ("Statut", self.menu_statut),
        )
        for col, (libelle, widget) in enumerate(champs_l1):
            ctk.CTkLabel(
                section_filtres,
                text=libelle,
                font=POLICE_TEXTE,
                text_color=TEXTE_SECONDAIRE,
                anchor="w",
            ).grid(row=1, column=col, sticky="w", padx=16, pady=(0, 2))
            widget.grid(row=2, column=col, sticky="ew", padx=16, pady=(0, 8))

        champs_l2 = (
            ("Service", self.menu_service),
            ("Urgence", self.menu_urgence),
            ("Date du", cadre_debut),
            ("Date au", cadre_fin),
        )
        for col, (libelle, widget) in enumerate(champs_l2):
            ctk.CTkLabel(
                section_filtres,
                text=libelle,
                font=POLICE_TEXTE,
                text_color=TEXTE_SECONDAIRE,
                anchor="w",
            ).grid(row=3, column=col, sticky="w", padx=16, pady=(0, 2))
            widget.grid(row=4, column=col, sticky="ew", padx=16, pady=(0, 8))

        for col in range(4):
            section_filtres.grid_columnconfigure(col, weight=1)

        barre_boutons = ctk.CTkFrame(section_filtres, fg_color="transparent")
        barre_boutons.grid(row=5, column=0, columnspan=4, sticky="ew", padx=16, pady=(0, 8))

        ctk.CTkButton(
            barre_boutons,
            text="Rechercher",
            font=POLICE_TEXTE,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._executer_recherche,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            barre_boutons,
            text="R\u00e9initialiser",
            font=POLICE_TEXTE,
            fg_color=SECONDAIRE,
            command=self._reinitialiser_filtres,
        ).pack(side="left")

        self.label_erreur = ctk.CTkLabel(
            section_filtres,
            text="",
            font=POLICE_TEXTE,
            text_color=ERREUR,
        )
        self.label_erreur.grid(
            row=6, column=0, columnspan=4, sticky="w", padx=16, pady=(0, 16)
        )

        self.label_compteur = ctk.CTkLabel(
            self,
            text="0 r\u00e9sultat(s)",
            font=POLICE_TEXTE,
            text_color=TEXTE_SECONDAIRE,
            anchor="w",
        )
        self.label_compteur.pack(fill="x", padx=24, pady=(0, 4))

        creer_entete_tableau(self, list(COLONNES_TABLEAU), LARGEURS_COLONNES)

        self.zone_liste = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0, height=320
        )
        self.zone_liste.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        self.bouton_export = ctk.CTkButton(
            self,
            text="Exporter r\u00e9sultats PDF",
            font=POLICE_TEXTE,
            fg_color=SECONDAIRE,
            state="disabled",
            command=self._exporter_pdf,
        )
        self.bouton_export.pack(anchor="w", padx=24, pady=(0, 16))

    def _collecter_filtres(self) -> dict[str, Any]:
        service = self.menu_service.get()
        return {
            "mot_cle": self.champ_mot_cle.get().strip() or None,
            "type_courrier": FILTRES_TYPE_RECHERCHE.get(self.menu_type.get()),
            "statut": FILTRES_STATUT_RECHERCHE.get(self.menu_statut.get()),
            "service": None if service == "Tous" else service,
            "urgence": FILTRES_URGENCE_RECHERCHE.get(self.menu_urgence.get()),
            "date_debut": lire_date_entry(self.champ_date_debut) or None,
            "date_fin": lire_date_entry(self.champ_date_fin) or None,
        }

    def _executer_recherche(self) -> None:
        self.label_erreur.configure(text="")
        filtres = self._collecter_filtres()
        try:
            self.resultats = rechercher_courriers(filtres)
            self.filtres_appliques = filtres
            self._afficher_resultats(self.resultats)
        except ValueError as erreur:
            self.label_erreur.configure(text=str(erreur))
        except RuntimeError:
            self.label_erreur.configure(text="Erreur lors de la recherche.")
            self._afficher_resultats([])

    def _relancer_recherche(self) -> None:
        if self.filtres_appliques:
            try:
                self.resultats = rechercher_courriers(self.filtres_appliques)
                self._afficher_resultats(self.resultats)
            except (ValueError, RuntimeError):
                pass

    def _reinitialiser_filtres(self) -> None:
        self.champ_mot_cle.delete(0, "end")
        self.menu_type.set("Tous")
        self.menu_statut.set("Tous")
        self.menu_service.set("Tous")
        self.menu_urgence.set("Tous")
        reinitialiser_date_entry(self.champ_date_debut, vider=True)
        reinitialiser_date_entry(self.champ_date_fin, vider=True)
        self.label_erreur.configure(text="")
        self.resultats = []
        self.filtres_appliques = {}
        self._afficher_resultats([])

    def _afficher_resultats(self, resultats: list[dict[str, Any]]) -> None:
        for widget in self.zone_liste.winfo_children():
            widget.destroy()

        nb = len(resultats)
        self.label_compteur.configure(text=f"{nb} r\u00e9sultat(s)")
        if resultats:
            self.bouton_export.configure(state="normal")
        else:
            self.bouton_export.configure(state="disabled")

        if not resultats:
            creer_etat_vide(
                self.zone_liste,
                "Aucun r\u00e9sultat",
                sous_message="Modifiez vos crit\u00e8res ou r\u00e9initialisez les filtres.",
            )
            return

        for index, courrier in enumerate(resultats):
            self._ajouter_ligne(courrier, index)

    def _ajouter_ligne(self, courrier: dict[str, Any], index: int) -> None:
        couleur_base = alterner_couleur_ligne(index)
        ligne = ctk.CTkFrame(
            self.zone_liste,
            fg_color=couleur_base,
            corner_radius=4,
        )
        ligne.pack(fill="x", pady=1)
        configurer_grille_tableau(ligne, LARGEURS_COLONNES, colonne_extensible=4)
        configurer_survol_ligne(ligne, couleur_base)

        type_c = str(courrier.get("type", ""))
        statut = str(courrier.get("statut", ""))
        urgence = str(courrier.get("urgence", "normal"))
        contact = (
            courrier.get("expediteur")
            if type_c == "entrant"
            else courrier.get("destinataire")
        ) or "\u2014"
        service = (
            courrier.get("service_destinataire")
            if type_c == "entrant"
            else courrier.get("service_emetteur")
        ) or "\u2014"
        date_aff = courrier.get("date_reception") or (
            (courrier.get("created_at") or "")[:10]
        )
        objet_complet = str(courrier.get("objet", ""))
        objet_aff = tronquer_texte(objet_complet, 40)

        ctk.CTkLabel(
            ligne,
            text=str(courrier.get("numero", "")),
            font=POLICE_TEXTE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        ).grid(row=0, column=0, padx=4, pady=6, sticky="ew")

        ctk.CTkLabel(
            ligne,
            text=LIBELLES_TYPE.get(type_c, type_c),
            font=POLICE_TEXTE,
            text_color=COULEURS_TYPE.get(type_c, TEXTE_PRIMAIRE),
            anchor="w",
        ).grid(row=0, column=1, padx=4, pady=6, sticky="ew")

        ctk.CTkLabel(
            ligne,
            text=str(date_aff),
            font=POLICE_TEXTE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        ).grid(row=0, column=2, padx=4, pady=6, sticky="ew")

        contact_complet = str(contact)
        label_contact = ctk.CTkLabel(
            ligne,
            text=tronquer_texte(contact_complet, 40),
            font=POLICE_TEXTE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        )
        label_contact.grid(row=0, column=3, padx=4, pady=6, sticky="ew")
        lier_infobulle(label_contact, contact_complet)

        label_objet = ctk.CTkLabel(
            ligne,
            text=objet_aff,
            font=POLICE_TEXTE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        )
        label_objet.grid(row=0, column=4, padx=4, pady=6, sticky="ew")
        lier_infobulle(label_objet, objet_complet)

        ctk.CTkLabel(
            ligne,
            text=str(service),
            font=POLICE_TEXTE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        ).grid(row=0, column=5, padx=4, pady=6, sticky="ew")

        ctk.CTkLabel(
            ligne,
            text=LIBELLES_URGENCE.get(urgence, urgence),
            font=POLICE_TEXTE,
            text_color=COULEURS_URGENCE.get(urgence, TEXTE_PRIMAIRE),
            anchor="w",
        ).grid(row=0, column=6, padx=4, pady=6, sticky="ew")

        ctk.CTkLabel(
            ligne,
            text=LIBELLES_STATUT.get(statut, statut),
            font=POLICE_TEXTE,
            text_color=COULEURS_STATUT.get(statut, TEXTE_PRIMAIRE),
            anchor="w",
        ).grid(row=0, column=7, padx=4, pady=6, sticky="ew")

        ctk.CTkButton(
            ligne,
            text="Voir",
            width=50,
            height=28,
            font=POLICE_TEXTE,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=lambda cid=courrier["id"]: ouvrir_fiche_courrier(
                self,
                self.utilisateur,
                cid,
                self.couleur_contenu,
                self._relancer_recherche,
            ),
        ).grid(row=0, column=8, padx=4, pady=4)

    def _exporter_pdf(self) -> None:
        if not self.resultats:
            return
        chemin = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            title="Exporter le rapport de recherche",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="rapport_recherche.pdf",
        )
        if not chemin:
            return
        try:
            exporter_rapport_recherche(
                self.resultats,
                self.filtres_appliques,
                chemin,
                self.utilisateur["id"],
            )
        except RuntimeError:
            self.label_erreur.configure(text="Erreur lors de l'export PDF.")
