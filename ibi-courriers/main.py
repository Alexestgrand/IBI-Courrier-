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

is_fullscreen: bool = False
geometry_memorisee: str | None = None


def est_plein_ecran() -> bool:
    """Indique si la fenetre principale est en plein ecran."""
    return is_fullscreen


def basculer_plein_ecran(fenetre: ctk.CTk) -> None:
    """Bascule entre mode plein ecran et fenetre."""
    global is_fullscreen, geometry_memorisee
    if not is_fullscreen:
        geometry_memorisee = fenetre.geometry()
        fenetre.resizable(True, True)
        fenetre.attributes("-fullscreen", True)
        is_fullscreen = True
    else:
        fenetre.attributes("-fullscreen", False)
        if geometry_memorisee:
            fenetre.geometry(geometry_memorisee)
        else:
            _centrer_fenetre(fenetre)
        is_fullscreen = False


def _quitter_plein_ecran(fenetre: ctk.CTk) -> None:
    """Quitte le plein ecran sans fermer l'application."""
    if is_fullscreen:
        basculer_plein_ecran(fenetre)


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
    app.resizable(True, True)
    app.configure(fg_color=COULEUR_PRINCIPALE)
    _centrer_fenetre(app)

    app.bind("<F11>", lambda _e: basculer_plein_ecran(app))
    app.bind("<Escape>", lambda _e: _quitter_plein_ecran(app))

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
