# -*- coding: utf-8 -*-
"""Fiches detail partagees pour courriers entrants et sortants."""

import tkinter.filedialog as filedialog
from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from services.courriers import (
    changer_statut,
    obtenir_courrier,
    obtenir_historique,
    obtenir_statuts_possibles,
    regenerer_pdf_sortant,
)
from utils.audit import enregistrer_audit
from utils.constants import (
    ALIAS_STATUT_CAHIER,
    COULEURS_STATUT,
    LIBELLES_STATUT,
    LIBELLES_URGENCE,
)
from utils.exports import ouvrir_fichier_export
from utils.fichiers import ouvrir_fichier
from utils.pdf import exporter_courrier_pdf
from utils.theme import (
    ACCENT,
    ACCENT_HOVER,
    ERREUR,
    FOND_CARTE,
    POLICE_PETIT,
    POLICE_SOUS_TITRE,
    POLICE_TEXTE,
    RAYON_CARTE,
    SECONDAIRE,
    SEPARATEUR,
    TEXTE_PRIMAIRE,
    TEXTE_SECONDAIRE,
)
from views.ui_helpers import configurer_modale

VIDE = "\u2014"
FLECHE = "\u2192"


def _statut_canonique(statut: str | None) -> str:
    """Statut canonique en base (alias legacy traite -> valide)."""
    if not statut:
        return ""
    return ALIAS_STATUT_CAHIER.get(str(statut), str(statut))


def _libelle_statut(statut: str | None) -> str:
    """Libelle UI d'un statut (alias legacy traite -> valide)."""
    if not statut:
        return VIDE
    return LIBELLES_STATUT.get(_statut_canonique(statut), str(statut))


def ouvrir_fiche_courrier(
    parent: ctk.CTkFrame,
    utilisateur: dict[str, Any],
    courrier_id: int,
    couleur_contenu: str,
    on_refresh: Callable[[], None],
) -> None:
    """Ouvre la fiche detail selon le type de courrier."""
    try:
        courrier = obtenir_courrier(courrier_id)
    except RuntimeError:
        return
    if courrier is None:
        return
    if courrier.get("type") == "sortant":
        ouvrir_fiche_sortant(
            parent, utilisateur, courrier_id, couleur_contenu, on_refresh
        )
    else:
        ouvrir_fiche_entrant(
            parent, utilisateur, courrier_id, couleur_contenu, on_refresh
        )


def _creer_barre_retour(fenetre: ctk.CTkToplevel) -> None:
    barre = ctk.CTkFrame(fenetre, fg_color="transparent")
    barre.pack(fill="x", padx=16, pady=(12, 0))
    ctk.CTkButton(
        barre,
        text="\u2190 Retour \u00e0 la liste",
        font=POLICE_TEXTE,
        fg_color="transparent",
        hover_color=SECONDAIRE,
        text_color=TEXTE_SECONDAIRE,
        anchor="w",
        command=fenetre.destroy,
    ).pack(anchor="w")


def _creer_section(parent: ctk.CTkBaseClass, titre: str) -> ctk.CTkFrame:
    section = ctk.CTkFrame(parent, fg_color=FOND_CARTE, corner_radius=RAYON_CARTE)
    section.pack(fill="x", pady=(0, 12))
    ctk.CTkLabel(
        section,
        text=titre,
        font=POLICE_SOUS_TITRE,
        text_color=TEXTE_PRIMAIRE,
        anchor="w",
    ).pack(fill="x", padx=16, pady=(12, 8))
    contenu = ctk.CTkFrame(section, fg_color="transparent")
    contenu.pack(fill="x", padx=16, pady=(0, 12))
    return contenu


def ouvrir_fiche_entrant(
    parent: ctk.CTkFrame,
    utilisateur: dict[str, Any],
    courrier_id: int,
    couleur_contenu: str,
    on_refresh: Callable[[], None],
) -> None:
    """Ouvre la fiche detail d'un courrier entrant."""
    try:
        courrier = obtenir_courrier(courrier_id)
        historique = obtenir_historique(courrier_id)
    except RuntimeError:
        return

    if courrier is None:
        return

    fenetre = ctk.CTkToplevel(parent)
    fenetre.title(f"Courrier {courrier.get('numero', '')}")
    configurer_modale(fenetre, parent, 640, 720, couleur=couleur_contenu)

    _creer_barre_retour(fenetre)

    scroll = ctk.CTkScrollableFrame(fenetre, fg_color="transparent")
    scroll.pack(fill="both", expand=True, padx=16, pady=(8, 8))

    label_erreur = ctk.CTkLabel(
        scroll, text="", font=POLICE_TEXTE, text_color=ERREUR
    )
    label_erreur.pack(anchor="w", pady=(0, 8))

    statut = str(courrier.get("statut", ""))
    urgence = str(courrier.get("urgence", ""))

    section_infos = _creer_section(scroll, "Informations")
    infos = [
        ("Num\u00e9ro", courrier.get("numero", "")),
        ("Date r\u00e9ception", courrier.get("date_reception", "")),
        ("Exp\u00e9diteur", courrier.get("expediteur", "")),
        ("R\u00e9f\u00e9rence document", courrier.get("reference_document") or VIDE),
        ("Objet", courrier.get("objet", "")),
        ("Service destinataire", courrier.get("service_destinataire", "")),
        ("Urgence", LIBELLES_URGENCE.get(urgence, urgence)),
        ("Statut", _libelle_statut(statut)),
        ("Observations", courrier.get("observations") or VIDE),
        ("Pi\u00e8ce jointe", courrier.get("fichier_joint") or VIDE),
    ]
    for libelle, valeur in infos:
        couleur = (
            COULEURS_STATUT.get(_statut_canonique(statut), TEXTE_PRIMAIRE)
            if libelle == "Statut"
            else TEXTE_PRIMAIRE
        )
        ctk.CTkLabel(
            section_infos,
            text=f"{libelle} : {valeur}",
            font=POLICE_TEXTE,
            text_color=couleur,
            anchor="w",
            justify="left",
        ).pack(fill="x", pady=2)

    _afficher_historique(scroll, historique)
    _ajouter_changement_statut(
        scroll,
        fenetre,
        courrier_id,
        utilisateur,
        statut,
        label_erreur,
        on_refresh,
        lambda: ouvrir_fiche_entrant(
            parent, utilisateur, courrier_id, couleur_contenu, on_refresh
        ),
    )

    barre_actions = ctk.CTkFrame(fenetre, fg_color="transparent")
    barre_actions.pack(fill="x", padx=16, pady=(0, 16))

    if courrier.get("fichier_joint"):
        ctk.CTkButton(
            barre_actions,
            text="Ouvrir pi\u00e8ce jointe",
            font=POLICE_TEXTE,
            fg_color=SECONDAIRE,
            command=lambda: _ouvrir_piece(courrier["fichier_joint"], label_erreur),
        ).pack(side="left", padx=(0, 8))

    def exporter_pdf() -> None:
        chemin = filedialog.asksaveasfilename(
            parent=fenetre,
            title="Exporter en PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"{courrier.get('numero', 'courrier')}.pdf",
        )
        if not chemin:
            return
        try:
            courrier_actuel = obtenir_courrier(courrier_id)
            hist_actuel = obtenir_historique(courrier_id)
            if courrier_actuel is None:
                raise RuntimeError("Courrier introuvable.")
            exporter_courrier_pdf(courrier_actuel, hist_actuel, chemin)
            enregistrer_audit(
                utilisateur["id"],
                "export_pdf",
                f"Courrier {courrier.get('numero', '')}",
                "courriers",
            )
        except RuntimeError as erreur:
            label_erreur.configure(text=str(erreur))

    ctk.CTkButton(
        barre_actions,
        text="Exporter PDF",
        font=POLICE_TEXTE,
        fg_color=ACCENT,
        hover_color=ACCENT_HOVER,
        command=exporter_pdf,
    ).pack(side="left", padx=(0, 8))

    ctk.CTkButton(
        barre_actions,
        text="Fermer",
        font=POLICE_TEXTE,
        fg_color=SECONDAIRE,
        command=fenetre.destroy,
    ).pack(side="right")


def ouvrir_fiche_sortant(
    parent: ctk.CTkFrame,
    utilisateur: dict[str, Any],
    courrier_id: int,
    couleur_contenu: str,
    on_refresh: Callable[[], None],
) -> None:
    """Ouvre la fiche detail d'un courrier sortant."""
    try:
        courrier = obtenir_courrier(courrier_id)
        historique = obtenir_historique(courrier_id)
    except RuntimeError:
        return

    if courrier is None:
        return

    fenetre = ctk.CTkToplevel(parent)
    fenetre.title(f"Courrier {courrier.get('numero', '')}")
    configurer_modale(fenetre, parent, 660, 760, couleur=couleur_contenu)

    _creer_barre_retour(fenetre)

    scroll = ctk.CTkScrollableFrame(fenetre, fg_color="transparent")
    scroll.pack(fill="both", expand=True, padx=16, pady=(8, 8))

    label_erreur = ctk.CTkLabel(
        scroll, text="", font=POLICE_TEXTE, text_color=ERREUR
    )
    label_erreur.pack(anchor="w", pady=(0, 8))

    statut = str(courrier.get("statut", ""))
    urgence = str(courrier.get("urgence", ""))

    section_infos = _creer_section(scroll, "Informations")
    infos = [
        ("Num\u00e9ro", courrier.get("numero", "")),
        ("Date d'envoi", courrier.get("date_reception", "")),
        ("Destinataire", courrier.get("destinataire", "")),
        ("Adresse", courrier.get("adresse_destinataire") or VIDE),
        ("Objet", courrier.get("objet", "")),
        ("Service \u00e9metteur", courrier.get("service_emetteur", "")),
        ("Urgence", LIBELLES_URGENCE.get(urgence, urgence)),
        ("Statut", _libelle_statut(statut)),
        ("Corps", courrier.get("corps_courrier") or VIDE),
        ("Observations", courrier.get("observations") or VIDE),
        ("Pi\u00e8ce jointe", courrier.get("fichier_joint") or VIDE),
        ("PDF export", courrier.get("chemin_pdf") or VIDE),
    ]
    for libelle, valeur in infos:
        couleur = (
            COULEURS_STATUT.get(_statut_canonique(statut), TEXTE_PRIMAIRE)
            if libelle == "Statut"
            else TEXTE_PRIMAIRE
        )
        ctk.CTkLabel(
            section_infos,
            text=f"{libelle} : {valeur}",
            font=POLICE_TEXTE,
            text_color=couleur,
            anchor="w",
            justify="left",
            wraplength=580,
        ).pack(fill="x", pady=2)

    _afficher_historique(scroll, historique)
    _ajouter_changement_statut(
        scroll,
        fenetre,
        courrier_id,
        utilisateur,
        statut,
        label_erreur,
        on_refresh,
        lambda: ouvrir_fiche_sortant(
            parent, utilisateur, courrier_id, couleur_contenu, on_refresh
        ),
    )

    barre_actions = ctk.CTkFrame(fenetre, fg_color="transparent")
    barre_actions.pack(fill="x", padx=16, pady=(0, 16))

    def reimprimer() -> None:
        try:
            chemin = regenerer_pdf_sortant(courrier_id, utilisateur["id"])
            ouvrir_fichier_export(chemin)
        except (ValueError, RuntimeError) as erreur:
            label_erreur.configure(text=str(erreur))

    ctk.CTkButton(
        barre_actions,
        text="R\u00e9imprimer PDF",
        font=POLICE_TEXTE,
        fg_color=ACCENT,
        hover_color=ACCENT_HOVER,
        command=reimprimer,
    ).pack(side="left", padx=(0, 8))

    if courrier.get("fichier_joint"):
        ctk.CTkButton(
            barre_actions,
            text="Ouvrir pi\u00e8ce jointe",
            font=POLICE_TEXTE,
            fg_color=SECONDAIRE,
            command=lambda: _ouvrir_piece(courrier["fichier_joint"], label_erreur),
        ).pack(side="left", padx=(0, 8))

    ctk.CTkButton(
        barre_actions,
        text="Fermer",
        font=POLICE_TEXTE,
        fg_color=SECONDAIRE,
        command=fenetre.destroy,
    ).pack(side="right")


def _afficher_historique(
    scroll: ctk.CTkScrollableFrame, historique: list[dict[str, Any]]
) -> None:
    section = _creer_section(scroll, "Historique des statuts")
    if not historique:
        ctk.CTkLabel(
            section,
            text="Aucun changement enregistr\u00e9.",
            font=POLICE_PETIT,
            text_color=TEXTE_SECONDAIRE,
            anchor="w",
        ).pack(fill="x", pady=2)
        return

    for index, entree in enumerate(historique):
        if index > 0:
            ctk.CTkFrame(section, height=1, fg_color=SEPARATEUR).pack(
                fill="x", pady=4
            )
        ancien = entree.get("ancien_statut")
        lib_ancien = _libelle_statut(ancien) if ancien else VIDE
        nouveau = entree.get("nouveau_statut", "")
        lib_nouveau = _libelle_statut(nouveau)
        utilisateur_hist = ""
        if entree.get("prenom") or entree.get("nom"):
            utilisateur_hist = (
                f" \u2014 {entree.get('prenom', '')} {entree.get('nom', '')}"
            )
        texte = (
            f"{entree.get('date', '')} : {lib_ancien} {FLECHE} {lib_nouveau}"
            f"{utilisateur_hist}"
        )
        if entree.get("observation"):
            texte += f" ({entree['observation']})"
        ctk.CTkLabel(
            section,
            text=texte,
            font=POLICE_PETIT,
            text_color=TEXTE_SECONDAIRE,
            anchor="w",
        ).pack(fill="x", pady=2)


def _ajouter_changement_statut(
    scroll: ctk.CTkScrollableFrame,
    fenetre: ctk.CTkToplevel,
    courrier_id: int,
    utilisateur: dict[str, Any],
    statut: str,
    label_erreur: ctk.CTkLabel,
    on_refresh: Callable[[], None],
    rouvrir_fiche: Callable[[], None],
) -> None:
    role = str(utilisateur.get("role", ""))
    statuts_possibles = obtenir_statuts_possibles(role, statut)
    statuts_libelles = {
        LIBELLES_STATUT[s]: s for s in statuts_possibles if s in LIBELLES_STATUT
    }

    if not statuts_libelles:
        return

    section = _creer_section(scroll, "Changer le statut")
    frame_statut = ctk.CTkFrame(section, fg_color="transparent")
    frame_statut.pack(fill="x", pady=4)

    menu_statut = ctk.CTkOptionMenu(
        frame_statut,
        values=list(statuts_libelles.keys()),
        font=POLICE_TEXTE,
    )
    menu_statut.pack(side="left", padx=(0, 8))
    menu_statut.set(list(statuts_libelles.keys())[0])

    champ_obs = ctk.CTkEntry(
        frame_statut,
        placeholder_text="Observation\u2026",
        font=POLICE_TEXTE,
        width=200,
    )
    champ_obs.pack(side="left", padx=(0, 8))

    def appliquer_statut() -> None:
        label_erreur.configure(text="")
        libelle_choisi = menu_statut.get()
        nouveau = statuts_libelles[libelle_choisi]
        try:
            changer_statut(
                courrier_id,
                nouveau,
                utilisateur["id"],
                champ_obs.get().strip() or None,
                role,
            )
            fenetre.destroy()
            on_refresh()
            rouvrir_fiche()
        except ValueError as erreur:
            label_erreur.configure(text=str(erreur))
        except RuntimeError:
            label_erreur.configure(text="Erreur lors du changement de statut.")

    ctk.CTkButton(
        frame_statut,
        text="Appliquer",
        font=POLICE_TEXTE,
        fg_color=ACCENT,
        hover_color=ACCENT_HOVER,
        command=appliquer_statut,
    ).pack(side="left")


def _ouvrir_piece(chemin_relatif: str, label_erreur: ctk.CTkLabel) -> None:
    try:
        ouvrir_fichier(chemin_relatif)
    except RuntimeError as erreur:
        label_erreur.configure(text=str(erreur))
