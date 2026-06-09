# -*- coding: utf-8 -*-
"""Vue d'administration des utilisateurs (reservee aux admins)."""

from typing import Any

import customtkinter as ctk

from services.auth import generer_mot_de_passe_temporaire
from services.utilisateurs import (
    basculer_actif_utilisateur_admin,
    creer_utilisateur_admin,
    lister_utilisateurs,
    mettre_a_jour_utilisateur_admin,
    obtenir_journal_audit,
    reinitialiser_mot_de_passe_admin,
)
from utils.constants import (
    COULEURS_ROLE,
    FILTRES_MODULE_AUDIT,
    FILTRES_ROLE_UTILISATEURS,
    LIBELLES_ROLE_UI,
    ROLES_VALIDES,
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
    SEPARATEUR,
    SUCCES,
    TEXTE_PRIMAIRE,
    TEXTE_SECONDAIRE,
)
from views.ui_helpers import (
    afficher_modale_confirmation,
    afficher_modale_message,
    alterner_couleur_ligne,
    configurer_grille_tableau,
    configurer_modale,
    creer_barre_titre,
    creer_entete_tableau,
    creer_etat_vide,
    lier_infobulle,
    packer_barre_actions,
    tronquer_texte,
)

LIBELLES_ROLE_MENU: list[str] = [LIBELLES_ROLE_UI[r] for r in ROLES_VALIDES]
ROLE_DEPUIS_LIBELLE: dict[str, str] = {v: k for k, v in LIBELLES_ROLE_UI.items()}

LARGEURS_COLONNES = (150, 180, 80, 70, 130, 200)
COLONNES_UTILISATEURS = (
    "Nom complet",
    "Email",
    "R\u00f4le",
    "Statut",
    "Derni\u00e8re connexion",
    "Actions",
)
LARGEURS_JOURNAL = (100, 130, 100, 80, 200)
COLONNES_JOURNAL = ("Date", "Utilisateur", "Action", "Module", "D\u00e9tail")
COULEUR_INACTIF = "#95A5A6"


class UtilisateursView(ctk.CTkFrame):
    """Gestion des utilisateurs et journal d'audit."""

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
        self.recherche_actuelle = ""
        self.filtre_role_actuel: str | None = None
        self.filtre_module_audit: str | None = None
        self.pack(fill="both", expand=True)

        if utilisateur.get("role") != "admin":
            ctk.CTkLabel(
                self,
                text="Acc\u00e8s r\u00e9serv\u00e9 aux administrateurs",
                font=POLICE_SOUS_TITRE,
                text_color=ERREUR,
            ).pack(pady=48, padx=32)
            return

        self._construire_interface()
        self.charger_liste()
        self.charger_journal()

    def _construire_interface(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True)

        _, zone_actions = creer_barre_titre(scroll, "Gestion des utilisateurs")

        self.champ_recherche = ctk.CTkEntry(
            zone_actions,
            placeholder_text="Nom ou email\u2026",
            font=POLICE_TEXTE,
            width=200,
        )
        self.champ_recherche.bind("<KeyRelease>", self._on_recherche_key)

        bouton_rechercher = ctk.CTkButton(
            zone_actions,
            text="Rechercher",
            font=POLICE_TEXTE,
            width=90,
            fg_color=SECONDAIRE,
            command=self._lancer_recherche,
        )

        self.menu_filtre_role = ctk.CTkOptionMenu(
            zone_actions,
            values=list(FILTRES_ROLE_UTILISATEURS.keys()),
            font=POLICE_TEXTE,
            command=self._appliquer_filtre_role,
        )
        self.menu_filtre_role.set("Tous")

        packer_barre_actions(
            zone_actions,
            [self.champ_recherche, bouton_rechercher, self.menu_filtre_role],
            bouton_primaire=("Nouvel utilisateur", self.ouvrir_formulaire_nouveau),
        )

        creer_entete_tableau(scroll, list(COLONNES_UTILISATEURS), LARGEURS_COLONNES)

        self.zone_liste = ctk.CTkScrollableFrame(
            scroll, fg_color="transparent", corner_radius=0, height=280
        )
        self.zone_liste.pack(fill="x", padx=24, pady=(0, 16))

        self._construire_section_journal(scroll)

    def _construire_section_journal(self, parent: ctk.CTkScrollableFrame) -> None:
        ctk.CTkFrame(parent, height=1, fg_color=SEPARATEUR).pack(
            fill="x", padx=24, pady=(8, 12)
        )

        barre_journal = ctk.CTkFrame(parent, fg_color="transparent")
        barre_journal.pack(fill="x", padx=24, pady=(0, 8))

        ctk.CTkLabel(
            barre_journal,
            text="Journal d'activit\u00e9",
            font=POLICE_SOUS_TITRE,
            text_color=TEXTE_PRIMAIRE,
        ).pack(side="left")

        ctk.CTkButton(
            barre_journal,
            text="Actualiser",
            font=POLICE_TEXTE,
            width=90,
            fg_color=SECONDAIRE,
            command=self.charger_journal,
        ).pack(side="right")

        self.menu_filtre_module = ctk.CTkOptionMenu(
            barre_journal,
            values=list(FILTRES_MODULE_AUDIT.keys()),
            font=POLICE_TEXTE,
            command=self._appliquer_filtre_module,
        )
        self.menu_filtre_module.set("Tous")
        self.menu_filtre_module.pack(side="right", padx=(8, 0))

        creer_entete_tableau(parent, list(COLONNES_JOURNAL), LARGEURS_JOURNAL)

        self.zone_journal = ctk.CTkScrollableFrame(
            parent, fg_color="transparent", corner_radius=0, height=220
        )
        self.zone_journal.pack(fill="x", padx=24, pady=(0, 24))

    def _appliquer_filtre_role(self, choix: str) -> None:
        self.filtre_role_actuel = FILTRES_ROLE_UTILISATEURS.get(choix)
        self.charger_liste()

    def _appliquer_filtre_module(self, choix: str) -> None:
        self.filtre_module_audit = FILTRES_MODULE_AUDIT.get(choix)
        self.charger_journal()

    def _on_recherche_key(self, _event: object) -> None:
        self.recherche_actuelle = self.champ_recherche.get().strip()
        self.charger_liste()

    def _lancer_recherche(self) -> None:
        self.recherche_actuelle = self.champ_recherche.get().strip()
        self.charger_liste()

    def charger_liste(self) -> None:
        """Recharge le tableau des utilisateurs."""
        if not hasattr(self, "zone_liste"):
            return

        for widget in self.zone_liste.winfo_children():
            widget.destroy()

        try:
            utilisateurs = lister_utilisateurs(
                self.recherche_actuelle or None,
                self.filtre_role_actuel,
            )
        except RuntimeError:
            ctk.CTkLabel(
                self.zone_liste,
                text="Erreur lors du chargement.",
                font=POLICE_TEXTE,
                text_color=ERREUR,
            ).pack(pady=12)
            return

        if not utilisateurs:
            creer_etat_vide(
                self.zone_liste,
                "Aucun utilisateur trouv\u00e9",
                sous_message="Modifiez votre recherche ou le filtre de r\u00f4le.",
            )
            return

        for index, utilisateur in enumerate(utilisateurs):
            self._ajouter_ligne_utilisateur(utilisateur, index)

    def _ajouter_ligne_utilisateur(
        self, user: dict[str, Any], index: int
    ) -> None:
        couleur_base = alterner_couleur_ligne(index)
        ligne = ctk.CTkFrame(
            self.zone_liste, fg_color=couleur_base, corner_radius=4
        )
        ligne.pack(fill="x", pady=2)
        configurer_grille_tableau(ligne, LARGEURS_COLONNES, colonne_extensible=0)

        nom_complet = f"{user.get('prenom', '')} {user.get('nom', '')}".strip()
        ctk.CTkLabel(
            ligne,
            text=nom_complet,
            font=POLICE_TEXTE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        ).grid(row=0, column=0, padx=6, pady=6, sticky="ew")

        ctk.CTkLabel(
            ligne,
            text=str(user.get("email", "")),
            font=POLICE_TEXTE,
            text_color=TEXTE_SECONDAIRE,
            anchor="w",
        ).grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        role = str(user.get("role", ""))
        ctk.CTkLabel(
            ligne,
            text=LIBELLES_ROLE_UI.get(role, role),
            font=(POLICE_PETIT[0], POLICE_PETIT[1], "bold"),
            text_color=TEXTE_PRIMAIRE,
            fg_color=COULEURS_ROLE.get(role, SECONDAIRE),
            corner_radius=4,
            width=70,
        ).grid(row=0, column=2, padx=6, pady=6)

        actif = int(user.get("actif", 1))
        ctk.CTkLabel(
            ligne,
            text="Actif" if actif else "Inactif",
            font=(POLICE_PETIT[0], POLICE_PETIT[1], "bold"),
            text_color=TEXTE_PRIMAIRE,
            fg_color=SUCCES if actif else COULEUR_INACTIF,
            corner_radius=4,
            width=60,
        ).grid(row=0, column=3, padx=6, pady=6)

        derniere = user.get("derniere_connexion") or "-"
        ctk.CTkLabel(
            ligne,
            text=str(derniere),
            font=POLICE_TEXTE,
            text_color=TEXTE_SECONDAIRE,
            anchor="w",
        ).grid(row=0, column=4, padx=6, pady=6, sticky="ew")

        actions = ctk.CTkFrame(ligne, fg_color="transparent")
        actions.grid(row=0, column=5, padx=4, pady=4, sticky="ew")

        ctk.CTkButton(
            actions,
            text="Modifier",
            width=70,
            height=HAUTEUR_BOUTON_LIGNE,
            font=POLICE_PETIT,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=lambda u=user: self.ouvrir_formulaire_modifier(u),
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            actions,
            text="MDP",
            width=40,
            height=HAUTEUR_BOUTON_LIGNE,
            font=POLICE_PETIT,
            fg_color=SECONDAIRE,
            command=lambda uid=user["id"]: self.ouvrir_modale_reset_mdp(uid),
        ).pack(side="left", padx=2)

        libelle_toggle = "D\u00e9sactiver" if actif else "Activer"
        ctk.CTkButton(
            actions,
            text=libelle_toggle,
            width=80,
            height=HAUTEUR_BOUTON_LIGNE,
            font=POLICE_PETIT,
            fg_color=DANGER if actif else SUCCES,
            command=lambda uid=user["id"], a=actif: self._toggle_actif(uid, a),
        ).pack(side="left", padx=2)

    def _toggle_actif(self, user_id: int, actif: int) -> None:
        def executer() -> None:
            try:
                basculer_actif_utilisateur_admin(user_id, self.utilisateur["id"])
                self.charger_liste()
            except ValueError as erreur:
                afficher_modale_message(
                    self, "Information", str(erreur), couleur=ERREUR
                )
            except RuntimeError:
                afficher_modale_message(
                    self,
                    "Information",
                    "Erreur lors du changement de statut.",
                    couleur=ERREUR,
                )

        if actif:
            afficher_modale_confirmation(
                self,
                "D\u00e9sactiver l'utilisateur",
                "D\u00e9sactiver cet utilisateur ? Il ne pourra plus se connecter.",
                confirmer_label="D\u00e9sactiver",
                on_confirmer=executer,
            )
        else:
            executer()

    def charger_journal(self) -> None:
        """Recharge le journal d'audit."""
        if not hasattr(self, "zone_journal"):
            return

        for widget in self.zone_journal.winfo_children():
            widget.destroy()

        try:
            entrees = obtenir_journal_audit(20, self.filtre_module_audit)
        except RuntimeError:
            ctk.CTkLabel(
                self.zone_journal,
                text="Erreur lors du chargement du journal.",
                font=POLICE_TEXTE,
                text_color=ERREUR,
            ).pack(pady=12)
            return

        if not entrees:
            creer_etat_vide(
                self.zone_journal,
                "Aucune entr\u00e9e",
                sous_message="Le journal sera aliment\u00e9 au fil des actions.",
            )
            return

        for index, entree in enumerate(entrees):
            self._ajouter_ligne_journal(entree, index)

    def _ajouter_ligne_journal(self, entree: dict[str, Any], index: int) -> None:
        couleur_base = alterner_couleur_ligne(index)
        ligne = ctk.CTkFrame(
            self.zone_journal, fg_color=couleur_base, corner_radius=4
        )
        ligne.pack(fill="x", pady=2)
        configurer_grille_tableau(ligne, LARGEURS_JOURNAL, colonne_extensible=4)

        prenom = entree.get("prenom")
        nom = entree.get("nom")
        if prenom or nom:
            utilisateur = f"{prenom or ''} {nom or ''}".strip()
        elif entree.get("email"):
            utilisateur = str(entree["email"])
        else:
            utilisateur = "-"

        detail_complet = str(entree.get("detail") or "")
        detail_aff = tronquer_texte(detail_complet, 60)

        colonnes = (
            str(entree.get("date", "")),
            utilisateur,
            str(entree.get("action", "")),
            str(entree.get("module") or "-"),
            detail_aff,
        )
        for col_index, texte in enumerate(colonnes):
            label = ctk.CTkLabel(
                ligne,
                text=texte,
                font=POLICE_PETIT,
                text_color=TEXTE_SECONDAIRE if col_index > 0 else TEXTE_PRIMAIRE,
                anchor="w",
            )
            label.grid(row=0, column=col_index, padx=6, pady=4, sticky="ew")
            if col_index == 4:
                lier_infobulle(label, detail_complet)

    def ouvrir_formulaire_nouveau(self) -> None:
        """Ouvre le formulaire modal de creation."""
        fenetre = ctk.CTkToplevel(self)
        fenetre.title("Nouvel utilisateur")
        configurer_modale(fenetre, self, 480, 520, couleur=self.couleur_contenu)

        label_erreur = ctk.CTkLabel(
            fenetre, text="", font=POLICE_TEXTE, text_color=ERREUR
        )
        label_erreur.pack(fill="x", padx=24, pady=(8, 0))

        boutons = ctk.CTkFrame(fenetre, fg_color="transparent")
        boutons.pack(side="bottom", fill="x", padx=24, pady=16)

        scroll = ctk.CTkScrollableFrame(fenetre, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=(4, 0))

        champs: dict[str, Any] = {}

        def ajouter_ligne(label: str, widget: ctk.CTkBaseClass) -> None:
            ctk.CTkLabel(
                scroll,
                text=label,
                font=POLICE_TEXTE,
                text_color=TEXTE_PRIMAIRE,
                anchor="w",
            ).pack(fill="x", padx=16, pady=(8, 2))
            widget.pack(fill="x", padx=16)

        champs["prenom"] = ctk.CTkEntry(scroll, font=POLICE_TEXTE)
        ajouter_ligne("Pr\u00e9nom *", champs["prenom"])

        champs["nom"] = ctk.CTkEntry(scroll, font=POLICE_TEXTE)
        ajouter_ligne("Nom *", champs["nom"])

        champs["email"] = ctk.CTkEntry(scroll, font=POLICE_TEXTE)
        ajouter_ligne("Email *", champs["email"])

        champs["role"] = ctk.CTkOptionMenu(
            scroll, values=LIBELLES_ROLE_MENU, font=POLICE_TEXTE
        )
        champs["role"].set(LIBELLES_ROLE_UI["reception"])
        ajouter_ligne("R\u00f4le *", champs["role"])

        frame_mdp = ctk.CTkFrame(scroll, fg_color="transparent")
        frame_mdp.pack(fill="x", padx=16, pady=(8, 0))
        ctk.CTkLabel(
            scroll,
            text="Mot de passe temporaire *",
            font=POLICE_TEXTE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(8, 2))

        champs["mdp"] = ctk.CTkEntry(frame_mdp, font=POLICE_TEXTE)
        champs["mdp"].pack(side="left", fill="x", expand=True)
        mdp_initial = generer_mot_de_passe_temporaire()
        champs["mdp"].insert(0, mdp_initial)

        def regenerer_mdp() -> None:
            champs["mdp"].delete(0, "end")
            champs["mdp"].insert(0, generer_mot_de_passe_temporaire())

        ctk.CTkButton(
            frame_mdp,
            text="G\u00e9n\u00e9rer",
            width=90,
            font=POLICE_TEXTE,
            fg_color=SECONDAIRE,
            command=regenerer_mdp,
        ).pack(side="right", padx=(8, 0))

        champs["actif"] = ctk.CTkSwitch(
            scroll, text="Compte actif", font=POLICE_TEXTE
        )
        champs["actif"].select()
        champs["actif"].pack(anchor="w", padx=16, pady=(12, 8))

        def creer() -> None:
            label_erreur.configure(text="")
            data = {
                "prenom": champs["prenom"].get(),
                "nom": champs["nom"].get(),
                "email": champs["email"].get(),
                "role": ROLE_DEPUIS_LIBELLE[champs["role"].get()],
                "mot_de_passe": champs["mdp"].get(),
                "actif": 1 if champs["actif"].get() else 0,
            }
            try:
                creer_utilisateur_admin(data, self.utilisateur["id"])
                fenetre.destroy()
                self.charger_liste()
                self.charger_journal()
            except ValueError as erreur:
                label_erreur.configure(text=str(erreur))
            except RuntimeError:
                label_erreur.configure(text="Erreur lors de la cr\u00e9ation.")

        ctk.CTkButton(
            boutons,
            text="Cr\u00e9er",
            font=POLICE_TEXTE,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=creer,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            boutons,
            text="Annuler",
            font=POLICE_TEXTE,
            fg_color=SECONDAIRE,
            command=fenetre.destroy,
        ).pack(side="right")

    def ouvrir_formulaire_modifier(self, user: dict[str, Any]) -> None:
        """Ouvre le formulaire modal de modification."""
        fenetre = ctk.CTkToplevel(self)
        fenetre.title("Modifier utilisateur")
        configurer_modale(fenetre, self, 480, 440, couleur=self.couleur_contenu)

        label_erreur = ctk.CTkLabel(
            fenetre, text="", font=POLICE_TEXTE, text_color=ERREUR
        )
        label_erreur.pack(fill="x", padx=24, pady=(8, 0))

        boutons = ctk.CTkFrame(fenetre, fg_color="transparent")
        boutons.pack(side="bottom", fill="x", padx=24, pady=16)

        scroll = ctk.CTkScrollableFrame(fenetre, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=(4, 0))

        champs: dict[str, Any] = {}
        user_id = user["id"]

        def ajouter_ligne(label: str, widget: ctk.CTkBaseClass) -> None:
            ctk.CTkLabel(
                scroll,
                text=label,
                font=POLICE_TEXTE,
                text_color=TEXTE_PRIMAIRE,
                anchor="w",
            ).pack(fill="x", padx=16, pady=(8, 2))
            widget.pack(fill="x", padx=16)

        champs["prenom"] = ctk.CTkEntry(scroll, font=POLICE_TEXTE)
        champs["prenom"].insert(0, str(user.get("prenom", "")))
        ajouter_ligne("Pr\u00e9nom *", champs["prenom"])

        champs["nom"] = ctk.CTkEntry(scroll, font=POLICE_TEXTE)
        champs["nom"].insert(0, str(user.get("nom", "")))
        ajouter_ligne("Nom *", champs["nom"])

        champs["email"] = ctk.CTkEntry(scroll, font=POLICE_TEXTE)
        champs["email"].insert(0, str(user.get("email", "")))
        ajouter_ligne("Email *", champs["email"])

        role_actuel = str(user.get("role", "reception"))
        champs["role"] = ctk.CTkOptionMenu(
            scroll, values=LIBELLES_ROLE_MENU, font=POLICE_TEXTE
        )
        champs["role"].set(LIBELLES_ROLE_UI.get(role_actuel, role_actuel))
        ajouter_ligne("R\u00f4le *", champs["role"])

        champs["actif"] = ctk.CTkSwitch(
            scroll, text="Compte actif", font=POLICE_TEXTE
        )
        if int(user.get("actif", 1)):
            champs["actif"].select()
        champs["actif"].pack(anchor="w", padx=16, pady=(12, 8))

        def enregistrer() -> None:
            label_erreur.configure(text="")
            data = {
                "prenom": champs["prenom"].get(),
                "nom": champs["nom"].get(),
                "email": champs["email"].get(),
                "role": ROLE_DEPUIS_LIBELLE[champs["role"].get()],
                "actif": 1 if champs["actif"].get() else 0,
            }
            try:
                mettre_a_jour_utilisateur_admin(
                    user_id, data, self.utilisateur["id"]
                )
                fenetre.destroy()
                self.charger_liste()
                self.charger_journal()
            except ValueError as erreur:
                label_erreur.configure(text=str(erreur))
            except RuntimeError:
                label_erreur.configure(text="Erreur lors de la mise \u00e0 jour.")

        ctk.CTkButton(
            boutons,
            text="Enregistrer",
            font=POLICE_TEXTE,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=enregistrer,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            boutons,
            text="Annuler",
            font=POLICE_TEXTE,
            fg_color=SECONDAIRE,
            command=fenetre.destroy,
        ).pack(side="right")

    def ouvrir_modale_reset_mdp(self, user_id: int) -> None:
        """Modale de reinitialisation du mot de passe."""
        fenetre = ctk.CTkToplevel(self)
        fenetre.title("R\u00e9initialiser le mot de passe")
        configurer_modale(fenetre, self, 460, 280, couleur=self.couleur_contenu)

        mdp_preview = generer_mot_de_passe_temporaire()

        ctk.CTkLabel(
            fenetre,
            text="Un mot de passe temporaire sera enregistr\u00e9 \u00e0 la confirmation.",
            font=POLICE_TEXTE,
            text_color=TEXTE_SECONDAIRE,
            wraplength=400,
        ).pack(padx=24, pady=(20, 8))

        champ_mdp = ctk.CTkEntry(fenetre, font=(POLICE_TEXTE[0], 14, "bold"))
        champ_mdp.pack(fill="x", padx=24, pady=8)
        champ_mdp.insert(0, mdp_preview)
        champ_mdp.configure(state="readonly")

        def copier() -> None:
            self.clipboard_clear()
            self.clipboard_append(mdp_preview)
            self.update()

        ctk.CTkButton(
            fenetre,
            text="Copier",
            font=POLICE_TEXTE,
            fg_color=SECONDAIRE,
            command=copier,
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            fenetre,
            text=(
                "Communiquez ce mot de passe \u00e0 l'utilisateur, "
                "il ne sera plus affich\u00e9."
            ),
            font=POLICE_PETIT,
            text_color=TEXTE_SECONDAIRE,
            wraplength=400,
        ).pack(padx=24, pady=(0, 8))

        label_erreur = ctk.CTkLabel(
            fenetre, text="", font=POLICE_TEXTE, text_color=ERREUR
        )
        label_erreur.pack()

        boutons = ctk.CTkFrame(fenetre, fg_color="transparent")
        boutons.pack(fill="x", padx=24, pady=16)

        def confirmer() -> None:
            try:
                reinitialiser_mot_de_passe_admin(
                    user_id,
                    self.utilisateur["id"],
                    mot_de_passe=mdp_preview,
                )
                fenetre.destroy()
                self.charger_journal()
            except ValueError as erreur:
                label_erreur.configure(text=str(erreur))
            except RuntimeError:
                label_erreur.configure(text="Erreur lors de la r\u00e9initialisation.")

        ctk.CTkButton(
            boutons,
            text="Confirmer",
            font=POLICE_TEXTE,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=confirmer,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            boutons,
            text="Annuler",
            font=POLICE_TEXTE,
            fg_color=SECONDAIRE,
            command=fenetre.destroy,
        ).pack(side="right")
