"""Génération PDF (courriers sortants, rapports de recherche)."""

import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.constants import LIBELLES_STATUT, LIBELLES_URGENCE

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo-ibi.png"


def _echapper_html(texte: str) -> str:
    return (
        str(texte)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


def _ajouter_logo(elements: list, largeur: float = 4.0) -> None:
    if LOGO_PATH.is_file():
        try:
            logo = Image(str(LOGO_PATH), width=largeur * cm, height=largeur * cm)
            logo.hAlign = "CENTER"
            elements.append(logo)
            elements.append(Spacer(1, 0.3 * cm))
        except Exception:
            pass


def generer_pdf_sortant(courrier: dict, chemin_absolu: str) -> str:
    """Génère le PDF d'un courrier sortant. Retourne le chemin absolu."""
    os.makedirs(os.path.dirname(chemin_absolu), exist_ok=True)

    doc = SimpleDocTemplate(
        chemin_absolu,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    style_groupe = ParagraphStyle(
        "Groupe",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#1B2A4A"),
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    style_titre = ParagraphStyle(
        "TitreIBI",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#1B2A4A"),
        alignment=TA_CENTER,
        spaceAfter=16,
    )
    style_meta = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=4,
    )
    style_dest = ParagraphStyle(
        "Dest",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        spaceAfter=12,
    )
    style_objet = ParagraphStyle(
        "Objet",
        parent=styles["Normal"],
        fontSize=11,
        fontName="Helvetica-Bold",
        spaceBefore=8,
        spaceAfter=12,
    )
    style_corps = ParagraphStyle(
        "Corps",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
    )
    style_pied = ParagraphStyle(
        "Pied",
        parent=styles["Normal"],
        fontSize=10,
        alignment=TA_RIGHT,
        spaceBefore=24,
    )

    elements: list = []
    _ajouter_logo(elements, 3.5)
    elements.append(Paragraph("GROUPE IBI — Côte d'Ivoire", style_groupe))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph("IBI COURRIERS", style_titre))

    numero = courrier.get("numero", "")
    date_str = courrier.get("date_reception") or datetime.now().strftime("%d/%m/%Y")
    urgence = LIBELLES_URGENCE.get(courrier.get("urgence", ""), courrier.get("urgence", ""))
    entite = courrier.get("entite_nom", "")

    elements.append(Paragraph(f"N° {numero} — {date_str}", style_meta))
    if entite:
        elements.append(Paragraph(f"Filiale : {entite}", style_meta))
    if urgence and urgence != "Normal":
        elements.append(Paragraph(f"Urgence : {urgence}", style_meta))
    elements.append(Spacer(1, 0.8 * cm))

    destinataire = courrier.get("destinataire", "")
    adresse = courrier.get("adresse_destinataire", "")
    elements.append(Paragraph(f"<b>{_echapper_html(destinataire)}</b>", style_dest))
    if adresse:
        elements.append(Paragraph(_echapper_html(adresse), style_dest))
    elements.append(Spacer(1, 0.5 * cm))

    objet = courrier.get("objet", "")
    elements.append(Paragraph(f"<b>Objet :</b> {_echapper_html(objet)}", style_objet))

    corps = courrier.get("corps_courrier", "") or ""
    for paragraphe in re.split(r"\n\s*\n", corps.strip()):
        if paragraphe.strip():
            elements.append(Paragraph(_echapper_html(paragraphe.strip()), style_corps))

    service = courrier.get("service_emetteur", "")
    elements.append(Spacer(1, 1 * cm))
    elements.append(Paragraph(f"Le service {service}", style_pied))
    elements.append(Paragraph("Groupe IBI", style_pied))

    signature_chemin = courrier.get("signature_chemin")
    signataire_nom = courrier.get("signataire_nom")
    if signature_chemin and os.path.isfile(signature_chemin):
        elements.append(Spacer(1, 0.5 * cm))
        try:
            sig = Image(signature_chemin, width=5 * cm, height=2 * cm)
            sig.hAlign = "RIGHT"
            elements.append(sig)
            if signataire_nom:
                style_sig = ParagraphStyle(
                    "SignatureNom",
                    parent=styles["Normal"],
                    fontSize=9,
                    alignment=TA_RIGHT,
                )
                elements.append(Paragraph(_echapper_html(signataire_nom), style_sig))
        except Exception:
            pass

    doc.build(elements)
    return chemin_absolu


def generer_rapport_recherche(
    resultats: list[dict],
    filtres: dict,
    chemin_sortie: str,
) -> str:
    """Génère un PDF rapport de recherche."""
    doc = SimpleDocTemplate(
        chemin_sortie,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    titre_style = ParagraphStyle(
        "TitreRapport",
        parent=styles["Heading1"],
        textColor=colors.HexColor("#1B2A4A"),
        spaceAfter=8,
        alignment=TA_CENTER,
    )

    elements: list = []
    _ajouter_logo(elements, 3.0)
    elements.append(Paragraph("IBI COURRIERS", titre_style))
    elements.append(Paragraph("Rapport de recherche", styles["Heading2"]))
    elements.append(
        Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            styles["Normal"],
        )
    )
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("<b>Filtres appliqués</b>", styles["Heading3"]))

    libelles_type = {"entrant": "Entrant", "sortant": "Sortant"}
    for ligne in [
        f"Mot-clé : {filtres.get('mot_cle') or '—'}",
        f"Type : {libelles_type.get(filtres.get('type_courrier'), 'Tous')}",
        f"Statut : {LIBELLES_STATUT.get(filtres.get('statut'), filtres.get('statut') or 'Tous')}",
        f"Service : {filtres.get('service') or 'Tous'}",
        f"Urgence : {LIBELLES_URGENCE.get(filtres.get('urgence'), filtres.get('urgence') or 'Toutes')}",
        f"Date du : {filtres.get('date_debut') or '—'}",
        f"Date au : {filtres.get('date_fin') or '—'}",
    ]:
        elements.append(Paragraph(ligne, styles["Normal"]))

    elements.append(Spacer(1, 0.3 * cm))
    elements.append(
        Paragraph(f"<b>Nombre total : {len(resultats)} courrier(s)</b>", styles["Normal"])
    )
    elements.append(Spacer(1, 0.5 * cm))

    entetes = ["N°", "Type", "Date", "Contact", "Objet", "Statut"]
    donnees = [entetes]
    for c in resultats:
        type_c = c.get("type", "")
        contact = c.get("expediteur") if type_c == "entrant" else c.get("destinataire")
        date_aff = c.get("date_reception") or str(c.get("created_at", ""))[:10]
        donnees.append(
            [
                c.get("numero", ""),
                "Entrant" if type_c == "entrant" else "Sortant",
                date_aff or "—",
                (contact or "—")[:30],
                (c.get("objet") or "—")[:40],
                LIBELLES_STATUT.get(c.get("statut"), c.get("statut", "")),
            ]
        )

    table = Table(
        donnees,
        colWidths=[2.8 * cm, 1.8 * cm, 2.2 * cm, 3.5 * cm, 5 * cm, 2.2 * cm],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B2A4A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)
    return chemin_sortie


MOIS_FR = (
    "",
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)


def generer_rapport_mensuel(stats: dict, chemin_sortie: str) -> str:
    """Génère le rapport mensuel d'activité (PDF)."""
    doc = SimpleDocTemplate(
        chemin_sortie,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    titre_style = ParagraphStyle(
        "TitreMensuel",
        parent=styles["Heading1"],
        textColor=colors.HexColor("#1B2A4A"),
        spaceAfter=8,
        alignment=TA_CENTER,
    )

    annee = stats["annee"]
    mois = stats["mois"]
    libelle_mois = MOIS_FR[mois] if 1 <= mois <= 12 else str(mois)

    elements: list = []
    _ajouter_logo(elements, 3.0)
    elements.append(Paragraph("IBI COURRIERS", titre_style))
    elements.append(
        Paragraph(
            f"Rapport mensuel — {libelle_mois} {annee}",
            styles["Heading2"],
        )
    )
    elements.append(
        Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            styles["Normal"],
        )
    )
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(
        Paragraph(
            f"<b>Total courriers enregistrés : {stats['total']}</b>",
            styles["Normal"],
        )
    )
    elements.append(Spacer(1, 0.4 * cm))

    def _tableau_titre(titre: str) -> None:
        elements.append(Paragraph(f"<b>{titre}</b>", styles["Heading3"]))
        elements.append(Spacer(1, 0.2 * cm))

    def _tableau_simple(lignes: list[list[str]], entetes: list[str]) -> None:
        donnees = [entetes, *lignes]
        table = Table(donnees, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B2A4A")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 0.4 * cm))

    par_service = stats.get("par_service") or {}
    if par_service:
        _tableau_titre("Volume par service")
        _tableau_simple(
            [[service, str(count)] for service, count in par_service.items()],
            ["Service", "Nombre"],
        )
    else:
        elements.append(Paragraph("Aucun courrier sur la période.", styles["Normal"]))
        elements.append(Spacer(1, 0.4 * cm))

    par_statut = stats.get("par_statut") or {}
    if par_statut:
        _tableau_titre("Répartition par statut")
        _tableau_simple(
            [
                [LIBELLES_STATUT.get(statut, statut), str(count)]
                for statut, count in par_statut.items()
            ],
            ["Statut", "Nombre"],
        )

    delais = stats.get("delais_moyens_jours") or {}
    if delais:
        _tableau_titre("Délai moyen de traitement (jours)")
        _tableau_simple(
            [[service, f"{jours} j"] for service, jours in delais.items()],
            ["Service", "Délai moyen"],
        )

    doc.build(elements)
    return chemin_sortie


def generer_rapport_recherche_temporaire(
    resultats: list[dict],
    filtres: dict,
) -> str:
    fd, chemin = tempfile.mkstemp(suffix=".pdf", prefix="rapport_recherche_")
    os.close(fd)
    return generer_rapport_recherche(resultats, filtres, chemin)
