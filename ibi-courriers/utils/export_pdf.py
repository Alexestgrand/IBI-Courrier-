"""Génération PDF des courriers sortants (lettre officielle)."""

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer

from database.db import RACINE_PROJET
from utils.chemin_app import chemin_asset
from utils.constants import LIBELLES_URGENCE
from utils.exports import DOSSIER_EXPORTS, creer_dossier_exports


def _chemin_logo() -> str | None:
    chemin = chemin_asset("assets/logo.png")
    return chemin if os.path.isfile(chemin) else None


def generer_courrier_sortant(
    courrier_data: dict,
    chemin_sortie: str | None = None,
) -> str:
    """Génère le PDF d'un courrier sortant et retourne le chemin relatif."""
    try:
        creer_dossier_exports()
        numero = courrier_data.get("numero", "SOR-0000")
        horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")

        if chemin_sortie is None:
            nom_fichier = f"{numero}_{horodatage}.pdf"
            chemin_absolu = os.path.join(DOSSIER_EXPORTS, nom_fichier)
            chemin_relatif = f"exports/{nom_fichier}"
        else:
            chemin_absolu = chemin_sortie
            chemin_relatif = os.path.relpath(chemin_absolu, RACINE_PROJET).replace(
                "\\", "/"
            )

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

        chemin_logo = _chemin_logo()
        if chemin_logo:
            try:
                logo = Image(chemin_logo, width=2.5 * cm, height=2.5 * cm)
                logo.hAlign = "CENTER"
                elements.append(logo)
                elements.append(Spacer(1, 0.2 * cm))
            except Exception:
                pass

        elements.append(Paragraph("GROUPE IBI", style_groupe))
        elements.append(Paragraph("IBI COURRIERS", style_titre))

        urgence = courrier_data.get("urgence", "normal")
        libelle_urgence = LIBELLES_URGENCE.get(str(urgence), str(urgence))
        elements.append(
            Paragraph(f"<b>Référence :</b> {numero}", style_meta)
        )
        elements.append(
            Paragraph(
                f"<b>Date d'envoi :</b> {courrier_data.get('date_reception', '')}",
                style_meta,
            )
        )
        elements.append(
            Paragraph(f"<b>Urgence :</b> {libelle_urgence}", style_meta)
        )
        elements.append(Spacer(1, 0.8 * cm))

        destinataire = courrier_data.get("destinataire", "")
        adresse = courrier_data.get("adresse_destinataire", "") or ""
        bloc_dest = destinataire
        if adresse:
            bloc_dest += f"<br/>{adresse.replace(chr(10), '<br/>')}"
        elements.append(Paragraph(bloc_dest, style_dest))
        elements.append(Spacer(1, 0.5 * cm))

        objet = courrier_data.get("objet", "")
        elements.append(Paragraph(f"Objet : {objet}", style_objet))

        corps = (courrier_data.get("corps_courrier") or "").replace("\n", "<br/>")
        elements.append(Paragraph(corps, style_corps))

        observations = courrier_data.get("observations")
        if observations:
            elements.append(
                Paragraph(
                    f"<i>Observations : {observations}</i>",
                    style_meta,
                )
            )

        service = courrier_data.get("service_emetteur", "")
        date_jour = datetime.now().strftime("%d/%m/%Y")
        elements.append(Spacer(1, 1.5 * cm))
        elements.append(Paragraph("_" * 40, style_pied))
        elements.append(Paragraph("Signature", style_pied))
        elements.append(Paragraph(f"Date : {date_jour}", style_pied))
        if service:
            elements.append(Paragraph(f"Service : {service}", style_pied))

        def _dessiner_confidentiel(canvas, _doc) -> None:
            if str(urgence) != "très urgent":
                return
            canvas.saveState()
            canvas.setFillColor(colors.HexColor("#E74C3C"))
            canvas.setFont("Helvetica-Bold", 9)
            canvas.drawString(2.5 * cm, A4[1] - 1.2 * cm, "CONFIDENTIEL")
            canvas.restoreState()

        doc.build(elements, onFirstPage=_dessiner_confidentiel)

        return chemin_relatif.replace("\\", "/")
    except Exception as erreur:
        raise RuntimeError("Échec de la génération du PDF sortant.") from erreur


def regenerer_ou_ouvrir_pdf_sortant(courrier: dict) -> str:
    """Régénère le PDF si absent ou manquant, retourne le chemin relatif."""
    chemin_pdf = courrier.get("chemin_pdf")
    if chemin_pdf:
        chemin_absolu = os.path.join(RACINE_PROJET, chemin_pdf.replace("\\", "/"))
        if os.path.isfile(chemin_absolu):
            return chemin_pdf

    return generer_courrier_sortant(courrier)


def generer_rapport_recherche(
    resultats: list[dict],
    filtres: dict,
    chemin_sortie: str,
) -> None:
    """Génère un PDF rapport de recherche avec filtres et tableau."""
    from reportlab.platypus import Table, TableStyle

    from utils.constants import (
        FILTRES_STATUT_RECHERCHE,
        FILTRES_TYPE_RECHERCHE,
        FILTRES_URGENCE_RECHERCHE,
        LIBELLES_STATUT,
        LIBELLES_TYPE,
        LIBELLES_URGENCE,
    )

    try:
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
        )
        elements: list = [
            Paragraph("IBI COURRIERS", titre_style),
            Paragraph("Rapport de recherche", styles["Heading2"]),
            Paragraph(
                f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
                styles["Normal"],
            ),
            Spacer(1, 0.5 * cm),
            Paragraph("<b>Filtres appliqués</b>", styles["Heading3"]),
        ]

        def _libelle_filtre(mapping: dict[str, str | None], valeur: str | None) -> str:
            if valeur is None:
                return "Tous"
            for libelle, cle in mapping.items():
                if cle == valeur:
                    return libelle
            return str(valeur)

        lignes_filtres = [
            f"Mot-clé : {filtres.get('mot_cle') or '—'}",
            f"Type : {_libelle_filtre(FILTRES_TYPE_RECHERCHE, filtres.get('type_courrier'))}",
            f"Statut : {_libelle_filtre(FILTRES_STATUT_RECHERCHE, filtres.get('statut'))}",
            f"Service : {filtres.get('service') or 'Tous'}",
            f"Urgence : {_libelle_filtre(FILTRES_URGENCE_RECHERCHE, filtres.get('urgence'))}",
            f"Date du : {filtres.get('date_debut') or '—'}",
            f"Date au : {filtres.get('date_fin') or '—'}",
        ]
        for ligne in lignes_filtres:
            elements.append(Paragraph(ligne, styles["Normal"]))

        elements.append(Spacer(1, 0.3 * cm))
        elements.append(
            Paragraph(
                f"<b>Nombre total : {len(resultats)} courrier(s)</b>",
                styles["Normal"],
            )
        )
        elements.append(Spacer(1, 0.5 * cm))

        entetes = [
            "N°",
            "Type",
            "Date",
            "Contact",
            "Objet",
            "Service",
            "Urgence",
            "Statut",
        ]
        donnees = [entetes]
        for courrier in resultats:
            type_c = str(courrier.get("type", ""))
            contact = (
                courrier.get("expediteur")
                if type_c == "entrant"
                else courrier.get("destinataire")
            ) or "—"
            service = (
                courrier.get("service_destinataire")
                if type_c == "entrant"
                else courrier.get("service_emetteur")
            ) or "—"
            date_aff = courrier.get("date_reception") or (
                (courrier.get("created_at") or "")[:10]
            )
            urgence = LIBELLES_URGENCE.get(
                str(courrier.get("urgence", "")), str(courrier.get("urgence", ""))
            )
            statut = LIBELLES_STATUT.get(
                str(courrier.get("statut", "")), str(courrier.get("statut", ""))
            )
            donnees.append(
                [
                    str(courrier.get("numero", ""))[:14],
                    LIBELLES_TYPE.get(type_c, type_c),
                    str(date_aff)[:10],
                    str(contact)[:18],
                    str(courrier.get("objet", ""))[:22],
                    str(service)[:14],
                    urgence[:10],
                    statut[:10],
                ]
            )

        table = Table(
            donnees,
            colWidths=[2.2 * cm, 1.6 * cm, 1.8 * cm, 2.8 * cm, 3.2 * cm, 2.2 * cm, 1.6 * cm, 1.8 * cm],
            repeatRows=1,
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B2A4A")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(table)
        doc.build(elements)
    except Exception as erreur:
        raise RuntimeError("Échec de la génération du rapport de recherche.") from erreur
