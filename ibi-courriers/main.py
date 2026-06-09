"""Point d'entrée de l'application IBI COURRIERS."""

import os
import sys

import customtkinter as ctk

from database.db import init_db
from utils.chemin_app import get_resource_path
from utils.scheduler import arreter_scheduler, start_scheduler
from views.login import LoginView

COULEUR_PRINCIPALE = "#1B2A4A"
LARGEUR_FENETRE = 1280
HAUTEUR_FENETRE = 720
TITRE_APPLICATION = "IBI COURRIERS"


def _centrer_fenetre(fenetre: ctk.CTk) -> None:
    fenetre.update_idletasks()
    pos_x = (fenetre.winfo_screenwidth() - LARGEUR_FENETRE) // 2
    pos_y = (fenetre.winfo_screenheight() - HAUTEUR_FENETRE) // 2
    fenetre.geometry(f"{LARGEUR_FENETRE}x{HAUTEUR_FENETRE}+{pos_x}+{pos_y}")


def main() -> None:
    try:
        init_db()
    except RuntimeError as erreur:
        print(f"Erreur d'initialisation : {erreur}", file=sys.stderr)
        sys.exit(1)

    start_scheduler()

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    app = ctk.CTk()
    app.title(TITRE_APPLICATION)
    app.geometry(f"{LARGEUR_FENETRE}x{HAUTEUR_FENETRE}")
    app.resizable(False, False)
    app.configure(fg_color=COULEUR_PRINCIPALE)
    _centrer_fenetre(app)

    LoginView(
        app,
        couleur_principale=COULEUR_PRINCIPALE,
        chemin_ressource=get_resource_path,
    )

    def _arreter_et_quitter() -> None:
        arreter_scheduler()
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", _arreter_et_quitter)

    app.mainloop()


if __name__ == "__main__":
    main()
