# -*- coding: utf-8 -*-
"""Composants et helpers UI reutilisables."""

from collections.abc import Callable

import customtkinter as ctk

from utils.theme import (
    ACCENT,
    ACCENT_HOVER,
    DANGER,
    ERREUR,
    FOND_CARTE,
    FOND_CONTENU,
    FOND_LIGNE,
    FOND_LIGNE_ALT,
    FOND_SURVOL,
    HAUTEUR_ENTETE_TABLE,
    POLICE_ENTETE,
    POLICE_PETIT,
    POLICE_TEXTE,
    POLICE_TITRE_PAGE,
    RAYON_MODALE,
    SECONDAIRE,
    TEXTE_PRIMAIRE,
    TEXTE_SECONDAIRE,
)

_label_statut: ctk.CTkLabel | None = None
_job_statut: str | None = None


def enregistrer_barre_statut(label: ctk.CTkLabel) -> None:
    """Enregistre le label de la barre de statut du dashboard."""
    global _label_statut
    _label_statut = label


def afficher_message_statut(texte: str, duree_ms: int = 3000) -> None:
    """Affiche un message temporaire dans la barre de statut."""
    global _job_statut
    if _label_statut is None or not _label_statut.winfo_exists():
        return
    if _job_statut is not None:
        try:
            _label_statut.after_cancel(_job_statut)
        except ValueError:
            pass
    _label_statut.configure(text=texte)
    _job_statut = _label_statut.after(
        duree_ms, lambda: _label_statut.configure(text="") if _label_statut else None
    )


def centrer_fenetre_modale(
    fenetre: ctk.CTkToplevel, largeur: int, hauteur: int
) -> None:
    """Centre une fenetre modale sur l'ecran."""
    fenetre.update_idletasks()
    pos_x = (fenetre.winfo_screenwidth() - largeur) // 2
    pos_y = (fenetre.winfo_screenheight() - hauteur) // 2
    fenetre.geometry(f"{largeur}x{hauteur}+{pos_x}+{pos_y}")


def configurer_modale(
    fenetre: ctk.CTkToplevel,
    parent: ctk.CTkBaseClass,
    largeur: int,
    hauteur: int,
    *,
    couleur: str = FOND_CONTENU,
) -> None:
    """Configure une modale : centrage, grab, Escape pour fermer."""
    fenetre.resizable(False, False)
    fenetre.configure(fg_color=couleur)
    fenetre.transient(parent.winfo_toplevel())
    fenetre.grab_set()
    centrer_fenetre_modale(fenetre, largeur, hauteur)
    fenetre.bind("<Escape>", lambda _e: fenetre.destroy())


def creer_barre_titre(
    parent: ctk.CTkFrame,
    titre: str,
) -> tuple[ctk.CTkFrame, ctk.CTkFrame]:
    """Barre de titre avec zone d'actions a droite (retourne barre, zone_actions)."""
    barre = ctk.CTkFrame(parent, fg_color="transparent")
    barre.pack(fill="x", padx=24, pady=(20, 12))

    ctk.CTkLabel(
        barre,
        text=titre,
        font=POLICE_TITRE_PAGE,
        text_color=TEXTE_PRIMAIRE,
    ).pack(side="left")

    zone_actions = ctk.CTkFrame(barre, fg_color="transparent")
    zone_actions.pack(side="right")

    return barre, zone_actions


def packer_barre_actions(
    zone_actions: ctk.CTkFrame,
    widgets: list[ctk.CTkBaseClass],
    *,
    bouton_primaire: tuple[str, Callable[[], None]] | None = None,
) -> None:
    """Dispose les widgets dans l'ordre gauche?droite, bouton primaire en dernier."""
    for widget in widgets:
        widget.pack(side="left", padx=(8, 0))

    if bouton_primaire is not None:
        libelle, commande = bouton_primaire
        ctk.CTkButton(
            zone_actions,
            text=libelle,
            font=POLICE_TEXTE,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=commande,
        ).pack(side="left", padx=(8, 0))


def creer_entete_tableau(
    parent: ctk.CTkBaseClass,
    colonnes: list[str],
    largeurs: tuple[int, ...],
) -> ctk.CTkFrame:
    """En-tete de tableau avec colonnes configurees."""
    entete = ctk.CTkFrame(
        parent, fg_color=FOND_CARTE, height=HAUTEUR_ENTETE_TABLE, corner_radius=4
    )
    entete.pack(fill="x", padx=24, pady=(0, 4))
    entete.pack_propagate(False)

    for index, (libelle, largeur) in enumerate(zip(colonnes, largeurs, strict=False)):
        poids = 1 if index == len(colonnes) // 2 else 0
        entete.grid_columnconfigure(index, minsize=largeur, weight=poids)
        ctk.CTkLabel(
            entete,
            text=libelle,
            font=POLICE_ENTETE,
            text_color=TEXTE_PRIMAIRE,
            anchor="w",
        ).grid(row=0, column=index, padx=6, pady=6, sticky="ew")

    return entete


def configurer_grille_tableau(
    conteneur: ctk.CTkFrame, largeurs: tuple[int, ...], colonne_extensible: int = 3
) -> None:
    """Configure les colonnes d'une ligne de tableau."""
    for index, largeur in enumerate(largeurs):
        conteneur.grid_columnconfigure(
            index, minsize=largeur, weight=1 if index == colonne_extensible else 0
        )


def creer_etat_vide(
    parent: ctk.CTkBaseClass,
    message: str,
    *,
    sous_message: str | None = None,
    icone: str = "\U0001f4ed",
) -> ctk.CTkFrame:
    """Etat vide avec message et sous-message optionnels."""
    cadre = ctk.CTkFrame(parent, fg_color="transparent")
    cadre.pack(pady=32)

    ctk.CTkLabel(
        cadre,
        text=icone,
        font=("Segoe UI", 32),
    ).pack(pady=(0, 8))

    ctk.CTkLabel(
        cadre,
        text=message,
        font=POLICE_TEXTE,
        text_color=TEXTE_SECONDAIRE,
    ).pack()

    if sous_message:
        ctk.CTkLabel(
            cadre,
            text=sous_message,
            font=POLICE_PETIT,
            text_color=TEXTE_SECONDAIRE,
        ).pack(pady=(4, 0))

    return cadre


def creer_badge(
    parent: ctk.CTkBaseClass,
    texte: str,
    couleur_fond: str,
    *,
    largeur: int | None = None,
) -> ctk.CTkLabel:
    """Badge colore compact."""
    kwargs: dict = {
        "text": texte,
        "font": (POLICE_PETIT[0], POLICE_PETIT[1], "bold"),
        "text_color": TEXTE_PRIMAIRE,
        "fg_color": couleur_fond,
        "corner_radius": 4,
    }
    if largeur is not None:
        kwargs["width"] = largeur
    badge = ctk.CTkLabel(parent, **kwargs)
    return badge


def appliquer_ligne_cliquable(
    ligne: ctk.CTkFrame, callback: Callable[[], None]
) -> None:
    """Rend une ligne cliquable (frame + tous les enfants)."""
    ligne.configure(cursor="hand2")

    def _clic(_event: object) -> None:
        callback()

    def _lier(widget: ctk.CTkBaseClass) -> None:
        if isinstance(widget, ctk.CTkButton):
            return
        widget.bind("<Button-1>", lambda _e: callback())
        for enfant in widget.winfo_children():
            _lier(enfant)

    ligne.bind("<Button-1>", _clic)
    for enfant in ligne.winfo_children():
        _lier(enfant)


def alterner_couleur_ligne(index: int) -> str:
    """Couleur zebra pour les lignes de tableau."""
    return FOND_LIGNE_ALT if index % 2 == 0 else FOND_LIGNE


def configurer_survol_ligne(ligne: ctk.CTkFrame, couleur_base: str) -> None:
    """Surbrillance au survol sans affecter les boutons."""

    def entrer(_event: object) -> None:
        ligne.configure(fg_color=FOND_SURVOL)

    def quitter(_event: object) -> None:
        ligne.configure(fg_color=couleur_base)

    ligne.bind("<Enter>", entrer)
    ligne.bind("<Leave>", quitter)


def tronquer_texte(texte: str, max_len: int) -> str:
    """Tronque un texte avec ellipsis."""
    texte = str(texte)
    if len(texte) <= max_len:
        return texte
    return texte[: max_len - 3] + "..."


def lier_infobulle(label: ctk.CTkLabel, texte_complet: str) -> None:
    """Affiche le texte complet dans la barre de statut au survol."""
    if texte_complet == tronquer_texte(texte_complet, 40):
        return

    def entrer(_event: object) -> None:
        afficher_message_statut(texte_complet, duree_ms=5000)

    label.bind("<Enter>", entrer)


def afficher_modale_message(
    parent: ctk.CTkBaseClass,
    titre: str,
    message: str,
    *,
    couleur: str = TEXTE_PRIMAIRE,
    bouton_ok: str = "OK",
) -> None:
    """Modale message uniforme."""
    fenetre = ctk.CTkToplevel(parent)
    fenetre.title(titre)
    configurer_modale(fenetre, parent, 440, 180)

    ctk.CTkLabel(
        fenetre,
        text=message,
        font=POLICE_TEXTE,
        text_color=couleur,
        wraplength=400,
        justify="left",
    ).pack(padx=24, pady=24)

    ctk.CTkButton(
        fenetre,
        text=bouton_ok,
        fg_color=ACCENT,
        hover_color=ACCENT_HOVER,
        command=fenetre.destroy,
    ).pack(pady=(0, 16))


def afficher_modale_confirmation(
    parent: ctk.CTkBaseClass,
    titre: str,
    message: str,
    *,
    confirmer_label: str = "Confirmer",
    annuler_label: str = "Annuler",
    couleur_confirmer: str = DANGER,
    on_confirmer: Callable[[], None],
) -> None:
    """Modale de confirmation uniforme."""
    fenetre = ctk.CTkToplevel(parent)
    fenetre.title(titre)
    configurer_modale(fenetre, parent, 480, 200)

    label_erreur = ctk.CTkLabel(
        fenetre, text="", font=POLICE_TEXTE, text_color=ERREUR
    )

    ctk.CTkLabel(
        fenetre,
        text=message,
        font=POLICE_TEXTE,
        text_color=TEXTE_PRIMAIRE,
        wraplength=440,
        justify="left",
    ).pack(padx=24, pady=(24, 8))

    label_erreur.pack()

    boutons = ctk.CTkFrame(fenetre, fg_color="transparent")
    boutons.pack(fill="x", padx=24, pady=16)

    def confirmer() -> None:
        try:
            on_confirmer()
            fenetre.destroy()
        except RuntimeError as erreur:
            label_erreur.configure(text=str(erreur))

    ctk.CTkButton(
        boutons,
        text=confirmer_label,
        font=POLICE_TEXTE,
        fg_color=couleur_confirmer,
        command=confirmer,
    ).pack(side="right", padx=(8, 0))

    ctk.CTkButton(
        boutons,
        text=annuler_label,
        font=POLICE_TEXTE,
        fg_color=SECONDAIRE,
        command=fenetre.destroy,
    ).pack(side="right")
