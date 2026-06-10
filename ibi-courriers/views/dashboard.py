# -*- coding: utf-8 -*-
"""Vue tableau de bord principal."""

import os
from collections.abc import Callable
from datetime import datetime
from typing import Any

import customtkinter as ctk
from PIL import Image

from services.stats import (
    obtenir_activite_recente,
    obtenir_courriers_urgents_non_traites,
    obtenir_stats_dashboard_complet,
    obtenir_stats_par_service,
)
from utils.audit import enregistrer_audit
from utils.constants import (
    COULEURS_STATUT,
    COULEURS_TYPE,
    LIBELLES_STATUT,
    VERSION_AFFICHAGE,
)
from utils.theme import (
    ACCENT,
    ACCENT_HOVER,
    DANGER,
    FOND_CARTE,
    FOND_CONTENU,
    FOND_PRINCIPAL,
    PAD_PAGE,
    POLICE_CHIFFRE,
    POLICE_ENTETE,
    POLICE_PETIT,
    POLICE_SOUS_TITRE,
    POLICE_TEXTE,
    POLICE_TITRE_PAGE,
    RAYON_CARTE,
    SEPARATEUR,
    TEXTE_PRIMAIRE,
    TEXTE_SECONDAIRE,
    LARGEUR_SIDEBAR,
)
from views.courriers_entrants import CourriersEntrantsView
from views.courriers_sortants import CourriersSortantsView
from views.fiche_courrier import ouvrir_fiche_courrier
from views.recherche import RechercheView
from views.sauvegardes import SauvegardesView
from views.ui_helpers import (
    afficher_message_statut,
    appliquer_ligne_cliquable,
    enregistrer_barre_statut,
    tronquer_texte,
)
from views.utilisateurs import UtilisateursView

INTERVALLE_HORLOGE_MS = 60_000
INTERVALLE_REFRESH_MS = 300_000

LIBELLES_ROLE: dict[str, str] = {
    "admin": "Administrateur",
    "dg": "Direction g\u00e9n\u00e9rale",
    "reception": "R\u00e9ception",
    "comptabilite": "Comptabilit\u00e9",
    "marche": "March\u00e9",
    "achat": "Achat",
}

# KPI traites_mois : statuts valide + archive (cahier « Traités » = validé en base)
CARTES_STATS: tuple[tuple[str, str, str], ...] = (
    ("total", "\U0001f4ca", "Total courriers"),
    ("en_attente", "\u23f3", "\u00c0 traiter"),
    ("urgents", "\U0001f525", "Urgents"),
    ("traites_mois", "\u2705", "Valid\u00e9s ce mois"),
)

ORDRE_STATUTS: tuple[str, ...] = (
    "en_attente",
    "transmis",
    "valide",
    "rejete",
    "archive",
)


class DashboardView:
    """Fenetre principale apres connexion."""

    def __init__(
        self,
        fenetre: ctk.CTk,
        *,
        utilisateur: dict[str, Any],
        couleur_principale: str,
        on_deconnexion: Callable[[], None],
        chemin_ressource: Callable[[str], str],
    ) -> None:
        self.fenetre = fenetre
        self.utilisateur = utilisateur
        self.couleur_principale = couleur_principale
        self.on_deconnexion = on_deconnexion
        self.chemin_ressource = chemin_ressource
        self.frame_actuel: ctk.CTkFrame | None = None
        self.section_active = "tableau_bord"
        self.boutons_nav: dict[str, ctk.CTkButton] = {}
        self._job_horloge: str | None = None
        self._job_refresh: str | None = None
        self._job_clignotement: str | None = None
        self._clignotement_actif = False
        self.label_horloge: ctk.CTkLabel | None = None
        self.badge_urgent: ctk.CTkLabel | None = None
        self._construire_interface()
        self.show_frame("tableau_bord")

    def _construire_interface(self) -> None:
        self.conteneur = ctk.CTkFrame(
            self.fenetre,
            fg_color=self.couleur_principale,
            corner_radius=0,
        )
        self.conteneur.pack(fill="both", expand=True)

        self.sidebar = ctk.CTkFrame(
            self.conteneur,
            width=LARGEUR_SIDEBAR,
            fg_color=FOND_PRINCIPAL,
            corner_radius=0,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self._construire_sidebar()

        self.zone_contenu = ctk.CTkFrame(
            self.conteneur,
            fg_color=FOND_CONTENU,
            corner_radius=0,
        )
        self.zone_contenu.pack(side="right", fill="both", expand=True)

        self.frame_contenu_interne = ctk.CTkFrame(
            self.zone_contenu, fg_color=FOND_CONTENU, corner_radius=0
        )
        self.frame_contenu_interne.pack(fill="both", expand=True)

        self.barre_statut = ctk.CTkLabel(
            self.zone_contenu,
            text="",
            height=24,
            fg_color=FOND_CARTE,
            text_color=TEXTE_SECONDAIRE,
            font=POLICE_PETIT,
            anchor="w",
        )
        self.barre_statut.pack(fill="x", side="bottom", padx=8, pady=(0, 4))
        enregistrer_barre_statut(self.barre_statut)

    def _construire_sidebar(self) -> None:
        entete = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        entete.pack(fill="x", padx=8, pady=(8, 0))

        zone_logo = ctk.CTkFrame(entete, fg_color="transparent")
        zone_logo.pack(side="left", fill="x", expand=True)
        self._ajouter_logo_sidebar(zone_logo)

        self._btn_plein_ecran = ctk.CTkButton(
            entete,
            text="\u26f6",
            width=32,
            height=32,
            font=POLICE_TEXTE,
            fg_color="transparent",
            hover_color=ACCENT_HOVER,
            text_color=TEXTE_SECONDAIRE,
            command=self._basculer_plein_ecran,
        )
        self._btn_plein_ecran.pack(side="right", padx=(4, 0))

        ctk.CTkLabel(
            self.sidebar,
            text="IBI COURRIERS",
            font=POLICE_SOUS_TITRE,
            text_color=TEXTE_PRIMAIRE,
        ).pack(padx=16, pady=(8, 4))

        initiales = (
            f"{str(self.utilisateur.get('prenom', ' '))[0]}"
            f"{str(self.utilisateur.get('nom', ' '))[0]}"
        ).upper()
        ctk.CTkLabel(
            self.sidebar,
            text=initiales,
            width=36,
            height=36,
            fg_color=ACCENT,
            corner_radius=18,
            font=POLICE_ENTETE,
            text_color=TEXTE_PRIMAIRE,
        ).pack(pady=(4, 4))

        role = LIBELLES_ROLE.get(
            str(self.utilisateur.get("role", "")),
            str(self.utilisateur.get("role", "")),
        )
        nom_utilisateur = (
            f"{self.utilisateur['prenom']} {self.utilisateur['nom']}\n{role}"
        )
        ctk.CTkLabel(
            self.sidebar,
            text=nom_utilisateur,
            font=POLICE_TEXTE,
            text_color=TEXTE_SECONDAIRE,
            justify="left",
        ).pack(padx=16, pady=(0, 12), anchor="w")

        ctk.CTkFrame(self.sidebar, height=1, fg_color=SEPARATEUR).pack(
            fill="x", padx=16, pady=(0, 12)
        )

        elements_nav: list[tuple[str, str]] = [
            ("tableau_bord", "\U0001f3e0  Tableau de bord"),
            ("courriers_entrants", "\U0001f4e5  Courriers entrants"),
            ("courriers_sortants", "\U0001f4e4  Courriers sortants"),
            ("recherche", "\U0001f50d  Recherche"),
        ]
        role = self.utilisateur.get("role")
        if role in ("admin", "dg"):
            elements_nav.append(("sauvegardes", "\U0001f4be  Sauvegardes"))
        if role == "admin":
            elements_nav.append(("utilisateurs", "\U0001f465  Utilisateurs"))

        for nom_section, libelle in elements_nav:
            bouton = ctk.CTkButton(
                self.sidebar,
                text=libelle,
                font=POLICE_TEXTE,
                anchor="w",
                fg_color="transparent",
                hover_color=ACCENT_HOVER,
                text_color=TEXTE_PRIMAIRE,
                height=36,
                command=lambda n=nom_section: self.show_frame(n),
            )
            bouton.pack(fill="x", padx=12, pady=2)
            self.boutons_nav[nom_section] = bouton

        ctk.CTkFrame(self.sidebar, height=1, fg_color=SEPARATEUR).pack(
            fill="x", padx=16, pady=12
        )

        ctk.CTkLabel(
            self.sidebar,
            text=f"IBI COURRIERS {VERSION_AFFICHAGE}",
            font=POLICE_PETIT,
            text_color=TEXTE_SECONDAIRE,
        ).pack(side="bottom", pady=(0, 4))

        ctk.CTkButton(
            self.sidebar,
            text="\U0001f6aa  D\u00e9connexion",
            font=POLICE_TEXTE,
            anchor="w",
            fg_color="transparent",
            hover_color=DANGER,
            text_color=TEXTE_PRIMAIRE,
            height=36,
            command=self._deconnecter,
        ).pack(fill="x", padx=12, pady=(0, 16), side="bottom")

    def _basculer_plein_ecran(self) -> None:
        from main import basculer_plein_ecran, est_plein_ecran

        basculer_plein_ecran(self.fenetre)
        self._btn_plein_ecran.configure(
            text="\u229f" if est_plein_ecran() else "\u26f6"
        )

    def _ajouter_logo_sidebar(self, parent: ctk.CTkFrame | None = None) -> None:
        conteneur = parent if parent is not None else self.sidebar
        chemin_logo = self.chemin_ressource("assets/logo.png")
        if not os.path.isfile(chemin_logo):
            return
        try:
            image = Image.open(chemin_logo)
            logo = ctk.CTkImage(light_image=image, dark_image=image, size=(48, 48))
            ctk.CTkLabel(conteneur, image=logo, text="").pack(
                side="left", padx=(8, 0), pady=(8, 4)
            )
        except OSError:
            pass

    def _annuler_timers_tableau_bord(self) -> None:
        """Annule les timers du tableau de bord."""
        self._clignotement_actif = False
        for job in (self._job_horloge, self._job_refresh, self._job_clignotement):
            if job is not None:
                try:
                    self.fenetre.after_cancel(job)
                except ValueError:
                    pass
        self._job_horloge = None
        self._job_refresh = None
        self._job_clignotement = None

    def show_frame(self, name: str) -> None:
        """Affiche une section de contenu (detruit la precedente)."""
        if self.section_active == "tableau_bord":
            self._annuler_timers_tableau_bord()

        if self.frame_actuel is not None:
            self.frame_actuel.destroy()

        self.frame_actuel = ctk.CTkFrame(
            self.frame_contenu_interne,
            fg_color=FOND_CONTENU,
            corner_radius=0,
        )
        self.frame_actuel.pack(fill="both", expand=True)

        constructeurs = {
            "tableau_bord": self._construire_tableau_bord,
            "courriers_entrants": lambda p: CourriersEntrantsView(
                p,
                utilisateur=self.utilisateur,
                couleur_contenu=FOND_CONTENU,
            ),
            "courriers_sortants": lambda p: CourriersSortantsView(
                p,
                utilisateur=self.utilisateur,
                couleur_contenu=FOND_CONTENU,
            ),
            "recherche": lambda p: RechercheView(
                p,
                utilisateur=self.utilisateur,
                couleur_contenu=FOND_CONTENU,
            ),
            "sauvegardes": lambda p: SauvegardesView(
                p,
                utilisateur=self.utilisateur,
                couleur_contenu=FOND_CONTENU,
            ),
            "utilisateurs": lambda p: UtilisateursView(
                p,
                utilisateur=self.utilisateur,
                couleur_contenu=FOND_CONTENU,
            ),
        }

        constructeur = constructeurs.get(name)
        if constructeur is None:
            self._construire_placeholder(self.frame_actuel, "Section introuvable")
        else:
            constructeur(self.frame_actuel)

        self.section_active = name
        self._mettre_a_jour_boutons_nav()

    def _mettre_a_jour_boutons_nav(self) -> None:
        for nom, bouton in self.boutons_nav.items():
            if nom == self.section_active:
                bouton.configure(fg_color=ACCENT)
            else:
                bouton.configure(fg_color="transparent")

    def _rafraichir_tableau_bord(self) -> None:
        """Recharge le contenu du tableau de bord."""
        if self.section_active != "tableau_bord" or self.frame_actuel is None:
            return
        self._annuler_timers_tableau_bord()
        for widget in self.frame_actuel.winfo_children():
            widget.destroy()
        self._construire_tableau_bord(self.frame_actuel)

    def _mettre_a_jour_horloge(self) -> None:
        if self.label_horloge is not None and self.label_horloge.winfo_exists():
            self.label_horloge.configure(
                text=datetime.now().strftime("%d/%m/%Y %H:%M")
            )
        if self.section_active == "tableau_bord":
            self._job_horloge = self.fenetre.after(
                INTERVALLE_HORLOGE_MS, self._mettre_a_jour_horloge
            )

    def _refresh_auto_tableau_bord(self) -> None:
        if self.section_active == "tableau_bord":
            self._rafraichir_tableau_bord()
            # _construire_tableau_bord relance les timers via _demarrer_timers_tableau_bord

    def _demarrer_timers_tableau_bord(self) -> None:
        self._job_horloge = self.fenetre.after(INTERVALLE_HORLOGE_MS, self._mettre_a_jour_horloge)
        self._job_refresh = self.fenetre.after(
            INTERVALLE_REFRESH_MS, self._refresh_auto_tableau_bord
        )

    def _demarrer_clignotement_badge(self) -> None:
        self._clignotement_actif = True

        def _clignoter() -> None:
            if not self._clignotement_actif:
                return
            if self.badge_urgent is None or not self.badge_urgent.winfo_exists():
                return
            couleur = self.badge_urgent.cget("fg_color")
            suivante = "#C0392B" if couleur == "#E74C3C" else "#E74C3C"
            self.badge_urgent.configure(fg_color=suivante)
            self._job_clignotement = self.fenetre.after(500, _clignoter)

        _clignoter()

    def _ouvrir_fiche_depuis_dashboard(self, courrier_id: int) -> None:
        if self.frame_actuel is None:
            return
        ouvrir_fiche_courrier(
            self.frame_actuel,
            self.utilisateur,
            courrier_id,
            FOND_CONTENU,
            self._rafraichir_tableau_bord,
        )

    def _construire_tableau_bord(self, parent: ctk.CTkFrame) -> None:
        self.label_horloge = None
        self.badge_urgent = None

        scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent", corner_radius=0
        )
        scroll.pack(fill="both", expand=True)

        try:
            stats_complet = obtenir_stats_dashboard_complet()
            cartes = stats_complet.get("cartes", {})
            repartition = stats_complet.get("repartition_statut", {})
            activite = obtenir_activite_recente(10)
            stats_services = obtenir_stats_par_service()
            urgents = obtenir_courriers_urgents_non_traites()
        except RuntimeError:
            cartes = {"total": 0, "en_attente": 0, "urgents": 0, "traites_mois": 0}
            repartition = {s: 0 for s in ORDRE_STATUTS}
            activite = []
            stats_services = {}
            urgents = []

        entete = ctk.CTkFrame(scroll, fg_color="transparent")
        entete.pack(fill="x", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            entete,
            text="Tableau de bord",
            font=POLICE_TITRE_PAGE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        ).pack(side="left")

        self.label_horloge = ctk.CTkLabel(
            entete,
            text=datetime.now().strftime("%d/%m/%Y %H:%M"),
            font=POLICE_TEXTE,
            text_color=TEXTE_SECONDAIRE,
        )
        self.label_horloge.pack(side="right")

        ctk.CTkLabel(
            scroll,
            text=f"Bonjour, {self.utilisateur.get('prenom', '')}",
            font=POLICE_TEXTE,
            text_color="#B8C4D9",
            anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 12))

        grille_cartes = ctk.CTkFrame(scroll, fg_color="transparent")
        grille_cartes.pack(fill="x", padx=24, pady=8)
        for index in range(4):
            grille_cartes.grid_columnconfigure(index, weight=1, uniform="cartes")

        for index, (cle, emoji, libelle) in enumerate(CARTES_STATS):
            self._creer_carte_stat(
                grille_cartes, cle, emoji, libelle, cartes.get(cle, 0), index
            )

        ligne2 = ctk.CTkFrame(scroll, fg_color="transparent")
        ligne2.pack(fill="x", padx=24, pady=12)
        ligne2.grid_columnconfigure(0, weight=1)
        ligne2.grid_columnconfigure(1, weight=1)

        col_gauche = ctk.CTkFrame(ligne2, fg_color="transparent")
        col_gauche.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._construire_repartition(col_gauche, repartition)

        col_droite = ctk.CTkFrame(ligne2, fg_color="transparent")
        col_droite.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self._construire_activite_recente(col_droite, activite)

        self._construire_section_urgents(scroll, urgents)
        self._construire_section_services(scroll, stats_services)

        self._demarrer_timers_tableau_bord()

    def _creer_carte_stat(
        self,
        parent: ctk.CTkFrame,
        cle: str,
        emoji: str,
        libelle: str,
        valeur: int,
        colonne: int,
    ) -> None:
        carte = ctk.CTkFrame(
            parent,
            fg_color=FOND_CARTE,
            corner_radius=RAYON_CARTE,
            height=120,
            border_width=1,
            border_color=SEPARATEUR,
        )
        carte.grid(row=0, column=colonne, padx=6, pady=6, sticky="nsew")

        ctk.CTkLabel(carte, text=emoji, font=("Segoe UI", 18)).pack(pady=(12, 0))
        ctk.CTkLabel(
            carte,
            text=str(valeur),
            font=POLICE_CHIFFRE,
            text_color=TEXTE_PRIMAIRE,
        ).pack(pady=(4, 0))
        ctk.CTkLabel(
            carte,
            text=libelle,
            font=POLICE_TEXTE,
            text_color=TEXTE_SECONDAIRE,
        ).pack(pady=(0, 4))
        if cle == "en_attente":
            ctk.CTkLabel(
                carte,
                text="dont transmis inclus",
                font=POLICE_PETIT,
                text_color=TEXTE_SECONDAIRE,
            ).pack(pady=(0, 8))
        if cle == "traites_mois":
            message_cahier = (
                "Inclut les courriers valid\u00e9s et archiv\u00e9s ce mois "
                "(ex-\u00ab trait\u00e9s \u00bb au sens cahier des charges)"
            )
            for widget in (carte, *carte.winfo_children()):
                widget.bind(
                    "<Enter>",
                    lambda _e, m=message_cahier: afficher_message_statut(m, 5000),
                )

    def _construire_repartition(
        self, parent: ctk.CTkFrame, repartition: dict[str, int]
    ) -> None:
        ctk.CTkLabel(
            parent,
            text="R\u00e9partition des courriers",
            font=POLICE_SOUS_TITRE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        max_val = max(repartition.values()) if repartition else 1
        if max_val <= 0:
            max_val = 1

        for statut in ORDRE_STATUTS:
            count = repartition.get(statut, 0)
            ligne = ctk.CTkFrame(parent, fg_color="transparent")
            ligne.pack(fill="x", pady=3)

            label_statut = ctk.CTkLabel(
                ligne,
                text=LIBELLES_STATUT.get(statut, statut),
                font=POLICE_TEXTE,
                text_color=TEXTE_PRIMAIRE,
                width=90,
                anchor="w",
            )
            label_statut.pack(side="left")
            if statut == "valide":
                label_statut.bind(
                    "<Enter>",
                    lambda _e: afficher_message_statut(
                        "Valid\u00e9 = \u00ab Trait\u00e9 \u00bb du cahier des charges "
                        "(statut valide en base)",
                        5000,
                    ),
                )

            barre = ctk.CTkProgressBar(
                ligne,
                height=14,
                corner_radius=7,
                progress_color=COULEURS_STATUT.get(statut, TEXTE_PRIMAIRE),
            )
            barre.set(count / max_val)
            barre.pack(side="left", fill="x", expand=True, padx=8)

            ctk.CTkLabel(
                ligne,
                text=str(count),
                font=POLICE_TEXTE,
                text_color="#B8C4D9",
                width=30,
            ).pack(side="right")

    def _construire_activite_recente(
        self, parent: ctk.CTkFrame, activite: list[dict[str, Any]]
    ) -> None:
        ctk.CTkLabel(
            parent,
            text="Activit\u00e9 r\u00e9cente",
            font=POLICE_SOUS_TITRE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        zone = ctk.CTkScrollableFrame(
            parent, fg_color=FOND_CARTE, corner_radius=RAYON_CARTE, height=220
        )
        zone.pack(fill="both", expand=True)

        if not activite:
            ctk.CTkLabel(
                zone,
                text="Aucune activit\u00e9.",
                font=POLICE_TEXTE,
                text_color="#B8C4D9",
            ).pack(pady=12)
            return

        for courrier in activite:
            self._ajouter_ligne_activite(zone, courrier)

    def _ajouter_ligne_activite(
        self, parent: ctk.CTkScrollableFrame, courrier: dict[str, Any]
    ) -> None:
        type_c = str(courrier.get("type", "entrant"))
        badge = "ENT" if type_c == "entrant" else "SORT"
        couleur_badge = COULEURS_TYPE.get(type_c, "#FFFFFF")
        statut = str(courrier.get("statut", ""))
        objet = tronquer_texte(str(courrier.get("objet", "")), 35)
        date_aff = courrier.get("date_reception") or (
            (courrier.get("created_at") or "")[:16]
        )

        ligne = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=4)
        ligne.pack(fill="x", pady=2, padx=4)

        ctk.CTkLabel(
            ligne,
            text=badge,
            font=("Segoe UI", 10, "bold"),
            text_color=couleur_badge,
            width=40,
        ).pack(side="left", padx=(4, 4))

        ctk.CTkLabel(
            ligne,
            text=objet,
            font=POLICE_TEXTE,
            text_color="#FFFFFF",
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            ligne,
            text=LIBELLES_STATUT.get(statut, statut),
            font=("Segoe UI", 10),
            text_color=COULEURS_STATUT.get(statut, "#B8C4D9"),
            width=70,
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            ligne,
            text=str(date_aff),
            font=("Segoe UI", 10),
            text_color="#B8C4D9",
            width=90,
        ).pack(side="right", padx=4)

        cid = courrier["id"]
        appliquer_ligne_cliquable(
            ligne, lambda c=cid: self._ouvrir_fiche_depuis_dashboard(c)
        )

    def _construire_section_urgents(
        self, parent: ctk.CTkScrollableFrame, urgents: list[dict[str, Any]]
    ) -> None:
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", padx=24, pady=(12, 8))

        entete = ctk.CTkFrame(section, fg_color="transparent")
        entete.pack(fill="x")

        ctk.CTkLabel(
            entete,
            text="Courriers tr\u00e8s urgents non trait\u00e9s",
            font=POLICE_SOUS_TITRE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        ).pack(side="left")

        if urgents:
            self.badge_urgent = ctk.CTkLabel(
                entete,
                text=f"! {len(urgents)}",
                font=("Segoe UI", 12, "bold"),
                text_color="#FFFFFF",
                fg_color="#E74C3C",
                corner_radius=6,
                width=40,
                height=24,
            )
            self.badge_urgent.pack(side="left", padx=12)
            self._demarrer_clignotement_badge()

        if not urgents:
            ctk.CTkLabel(
                section,
                text="Aucun courrier tr\u00e8s urgent en attente.",
                font=POLICE_TEXTE,
                text_color="#B8C4D9",
                anchor="w",
            ).pack(fill="x", pady=8)
            return

        for courrier in urgents:
            ligne = ctk.CTkFrame(section, fg_color="#1B2A4A", corner_radius=4)
            ligne.pack(fill="x", pady=2)

            statut = str(courrier.get("statut", ""))
            texte = (
                f"{courrier.get('numero', '')}  |  "
                f"{str(courrier.get('objet', ''))[:40]}  |  "
                f"{LIBELLES_STATUT.get(statut, statut)}"
            )
            ctk.CTkLabel(
                ligne,
                text=texte,
                font=POLICE_TEXTE,
                text_color="#FFFFFF",
                anchor="w",
            ).pack(fill="x", padx=8, pady=6)

            cid = courrier["id"]
            appliquer_ligne_cliquable(
                ligne, lambda c=cid: self._ouvrir_fiche_depuis_dashboard(c)
            )

    def _construire_section_services(
        self, parent: ctk.CTkScrollableFrame, stats_services: dict[str, int]
    ) -> None:
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", padx=24, pady=(8, 24))

        ctk.CTkLabel(
            section,
            text="Courriers par service ce mois",
            font=POLICE_SOUS_TITRE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        if not stats_services or all(v == 0 for v in stats_services.values()):
            ctk.CTkLabel(
                section,
                text="Aucun courrier enregistr\u00e9 ce mois par service.",
                font=POLICE_TEXTE,
                text_color="#B8C4D9",
                anchor="w",
            ).pack(fill="x")
            return

        max_val = max(stats_services.values()) or 1

        for nom, count in stats_services.items():
            ligne = ctk.CTkFrame(section, fg_color="transparent")
            ligne.pack(fill="x", pady=3)

            ctk.CTkLabel(
                ligne,
                text=nom,
                font=POLICE_TEXTE,
                text_color="#FFFFFF",
                width=140,
                anchor="w",
            ).pack(side="left")

            barre = ctk.CTkProgressBar(
                ligne, height=14, corner_radius=7, progress_color=ACCENT
            )
            barre.set(count / max_val)
            barre.pack(side="left", fill="x", expand=True, padx=8)

            ctk.CTkLabel(
                ligne,
                text=str(count),
                font=POLICE_TEXTE,
                text_color="#B8C4D9",
                width=30,
            ).pack(side="right")

    def _construire_placeholder(self, parent: ctk.CTkFrame, titre: str) -> None:
        ctk.CTkLabel(
            parent,
            text=titre,
            font=POLICE_TITRE_PAGE,
            text_color=TEXTE_PRIMAIRE,
        ).pack(pady=(32, 8), padx=32, anchor="w")

        ctk.CTkLabel(
            parent,
            text="Section en cours de d\u00e9veloppement.",
            font=POLICE_TEXTE,
            text_color=TEXTE_SECONDAIRE,
        ).pack(padx=32, anchor="w")

    def _deconnecter(self) -> None:
        self._annuler_timers_tableau_bord()
        try:
            enregistrer_audit(
                self.utilisateur["id"],
                "deconnexion",
                f"D\u00e9connexion de {self.utilisateur['email']}",
                "auth",
            )
        except RuntimeError:
            pass

        self.conteneur.destroy()
        self.on_deconnexion()
