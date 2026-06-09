"""Vue de connexion."""

import os
from collections.abc import Callable

import customtkinter as ctk
from PIL import Image

from services.auth import authentifier
from utils.theme import (
    ACCENT,
    ACCENT_HOVER,
    ERREUR,
    FOND_CONTENU,
    FOND_ERREUR,
    HAUTEUR_BOUTON,
    HAUTEUR_CHAMP,
    POLICE_TEXTE,
    POLICE_TITRE_PAGE,
    RAYON_MODALE,
    TEXTE_PRIMAIRE,
    TEXTE_SECONDAIRE,
)
from views.dashboard import DashboardView

MESSAGE_CHAMPS_VIDES = "Veuillez renseigner l'e-mail et le mot de passe."
MESSAGE_IDENTIFIANTS_INCORRECTS = "Identifiants incorrects"


class LoginView:
    """Interface de connexion à l'application."""

    def __init__(
        self,
        fenetre: ctk.CTk,
        *,
        couleur_principale: str,
        chemin_ressource: Callable[[str], str],
    ) -> None:
        self.fenetre = fenetre
        self.couleur_principale = couleur_principale
        self.chemin_ressource = chemin_ressource
        self._construire_interface()

    def _construire_interface(self) -> None:
        self.conteneur = ctk.CTkFrame(
            self.fenetre,
            fg_color=self.couleur_principale,
            corner_radius=0,
        )
        self.conteneur.pack(fill="both", expand=True)

        carte = ctk.CTkFrame(
            self.conteneur,
            width=420,
            height=520,
            corner_radius=RAYON_MODALE,
            fg_color=FOND_CONTENU,
        )
        carte.place(relx=0.5, rely=0.5, anchor="center")
        carte.pack_propagate(False)

        self._ajouter_logo(carte)

        ctk.CTkLabel(
            carte,
            text="IBI COURRIERS",
            font=POLICE_TITRE_PAGE,
            text_color=TEXTE_PRIMAIRE,
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            carte,
            text="Gestion électronique des courriers",
            font=POLICE_TEXTE,
            text_color=TEXTE_SECONDAIRE,
        ).pack(pady=(0, 24))

        ctk.CTkLabel(
            carte,
            text="Adresse e-mail",
            font=POLICE_TEXTE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        ).pack(fill="x", padx=32)

        self.champ_email = ctk.CTkEntry(
            carte,
            placeholder_text="admin@ibi.local",
            font=POLICE_TEXTE,
            height=HAUTEUR_CHAMP,
        )
        self.champ_email.pack(fill="x", padx=32, pady=(4, 16))
        self.champ_email.bind("<Return>", lambda _event: self._tenter_connexion())

        ctk.CTkLabel(
            carte,
            text="Mot de passe",
            font=POLICE_TEXTE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        ).pack(fill="x", padx=32)

        self.champ_mot_de_passe = ctk.CTkEntry(
            carte,
            placeholder_text="••••••••",
            show="•",
            font=POLICE_TEXTE,
            height=HAUTEUR_CHAMP,
        )
        self.champ_mot_de_passe.pack(fill="x", padx=32, pady=(4, 8))
        self.champ_mot_de_passe.bind(
            "<Return>", lambda _event: self._tenter_connexion()
        )

        self.cadre_erreur = ctk.CTkFrame(
            carte, fg_color=FOND_ERREUR, corner_radius=6, border_width=1, border_color=ERREUR
        )
        self.label_erreur = ctk.CTkLabel(
            self.cadre_erreur,
            text="",
            font=POLICE_TEXTE,
            text_color=ERREUR,
            wraplength=340,
        )
        self.label_erreur.pack(padx=12, pady=8)
        self.cadre_erreur.pack(fill="x", padx=32, pady=(0, 8))
        self.cadre_erreur.pack_forget()

        ctk.CTkButton(
            carte,
            text="Se connecter",
            font=POLICE_TEXTE,
            height=HAUTEUR_BOUTON,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self._tenter_connexion,
        ).pack(fill="x", padx=32, pady=(8, 24))

        self.fenetre.after(100, lambda: self.champ_email.focus())

    def _afficher_erreur(self, message: str) -> None:
        if message:
            self.label_erreur.configure(text=message)
            self.cadre_erreur.pack(fill="x", padx=32, pady=(0, 8))
        else:
            self.label_erreur.configure(text="")
            self.cadre_erreur.pack_forget()

    def _ajouter_logo(self, parent: ctk.CTkFrame) -> None:
        chemin_logo = self.chemin_ressource("assets/logo.png")
        if not os.path.isfile(chemin_logo):
            return
        try:
            image = Image.open(chemin_logo)
            logo = ctk.CTkImage(light_image=image, dark_image=image, size=(80, 80))
            ctk.CTkLabel(parent, image=logo, text="").pack(pady=(24, 8))
        except OSError:
            pass

    def _tenter_connexion(self) -> None:
        email = self.champ_email.get().strip()
        mot_de_passe = self.champ_mot_de_passe.get()

        if not email or not mot_de_passe:
            self._afficher_erreur(MESSAGE_CHAMPS_VIDES)
            return

        self._afficher_erreur("")

        try:
            utilisateur = authentifier(email, mot_de_passe)
        except RuntimeError:
            self._afficher_erreur("Erreur de connexion. Veuillez réessayer.")
            return

        if utilisateur is None:
            self._afficher_erreur(MESSAGE_IDENTIFIANTS_INCORRECTS)
            return

        self._ouvrir_dashboard(utilisateur)

    def _ouvrir_dashboard(self, utilisateur: dict) -> None:
        self.conteneur.destroy()
        DashboardView(
            self.fenetre,
            utilisateur=utilisateur,
            couleur_principale=self.couleur_principale,
            on_deconnexion=self._afficher_login,
            chemin_ressource=self.chemin_ressource,
        )

    def _afficher_login(self) -> None:
        LoginView(
            self.fenetre,
            couleur_principale=self.couleur_principale,
            chemin_ressource=self.chemin_ressource,
        )
