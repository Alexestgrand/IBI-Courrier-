"""Export PDF des courriers (ReportLab)."""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from utils.constants import LIBELLES_STATUT, LIBELLES_URGENCE


def exporter_courrier_pdf(
    courrier: dict,
    historique: list[dict],
    chemin_sortie: str,
) -> None:
    """Génère un PDF récapitulatif du courrier et de son historique."""
    try:
        doc = SimpleDocTemplate(
            chemin_sortie,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )
        styles = getSampleStyleSheet()
        titre_style = ParagraphStyle(
            "TitreIBI",
            parent=styles["Heading1"],
            textColor=colors.HexColor("#1B2A4A"),
            spaceAfter=12,
        )
        elements: list = [
            Paragraph("IBI COURRIERS", titre_style),
            Paragraph("Fiche courrier entrant", styles["Heading2"]),
            Spacer(1, 0.5 * cm),
        ]

        statut = LIBELLES_STATUT.get(
            str(courrier.get("statut", "")), str(courrier.get("statut", ""))
        )
        urgence = LIBELLES_URGENCE.get(
            str(courrier.get("urgence", "")), str(courrier.get("urgence", ""))
        )

        infos = [
            ["Numéro", courrier.get("numero", "")],
            ["Date réception", courrier.get("date_reception", "")],
            ["Expéditeur", courrier.get("expediteur", "")],
            ["Référence document", courrier.get("reference_document", "") or "—"],
            ["Objet", courrier.get("objet", "")],
            ["Service destinataire", courrier.get("service_destinataire", "")],
            ["Urgence", urgence],
            ["Statut", statut],
            ["Observations", courrier.get("observations", "") or "—"],
            ["Pièce jointe", courrier.get("fichier_joint", "") or "—"],
        ]
        table_infos = Table(infos, colWidths=[5 * cm, 12 * cm])
        table_infos.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8ECF2")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(table_infos)
        elements.append(Spacer(1, 1 * cm))
        elements.append(Paragraph("Historique des statuts", styles["Heading2"]))
        elements.append(Spacer(1, 0.3 * cm))

        lignes_hist = [["Date", "Ancien statut", "Nouveau statut", "Utilisateur", "Observation"]]
        for entree in historique:
            ancien = entree.get("ancien_statut")
            libelle_ancien = (
                LIBELLES_STATUT.get(ancien, ancien) if ancien else "—"
            )
            nouveau = entree.get("nouveau_statut", "")
            libelle_nouveau = LIBELLES_STATUT.get(nouveau, nouveau)
            utilisateur = ""
            if entree.get("prenom") or entree.get("nom"):
                utilisateur = f"{entree.get('prenom', '')} {entree.get('nom', '')}".strip()
            lignes_hist.append(
                [
                    entree.get("date", ""),
                    libelle_ancien,
                    libelle_nouveau,
                    utilisateur or "—",
                    entree.get("observation", "") or "—",
                ]
            )

        table_hist = Table(
            lignes_hist,
            colWidths=[3.5 * cm, 3 * cm, 3 * cm, 3.5 * cm, 4 * cm],
            repeatRows=1,
        )
        table_hist.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B2A4A")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("PADDING", (0, 0), (-1, -1), 5),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(table_hist)
        doc.build(elements)
    except Exception as erreur:
        raise RuntimeError("Échec de la génération du PDF.") from erreur
