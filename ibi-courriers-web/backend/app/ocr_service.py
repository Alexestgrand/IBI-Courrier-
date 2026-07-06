"""Extraction OCR / texte depuis scans et PDF."""

from __future__ import annotations

import io
import logging
import re
import shutil
from typing import Any

logger = logging.getLogger(__name__)

REF_PATTERNS = [
    re.compile(
        r"(?:r[ée]f(?:[ée]rence)?|ref\.?|n[°o])\s*[:\.]?\s*([A-Z0-9][A-Z0-9\-/_\.]{2,40})",
        re.IGNORECASE,
    ),
    re.compile(r"\b([A-Z]{2,5}[-/]\d{4,}[-/]?\d*)\b"),
]

OBJET_PATTERNS = [
    re.compile(r"objet\s*[:\-]\s*(.+)", re.IGNORECASE),
    re.compile(r"concernant\s*[:\-]?\s*(.+)", re.IGNORECASE),
]

EXPEDITEUR_PATTERNS = [
    re.compile(r"(?:de|exp[ée]diteur|sender)\s*[:\-]\s*(.+)", re.IGNORECASE),
    re.compile(r"(?:monsieur|madame|m\.|mme\.?|dr\.?)\s+(.+)", re.IGNORECASE),
]


def _tesseract_disponible() -> bool:
    return shutil.which("tesseract") is not None


def _ocr_image(contenu: bytes) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return ""

    if not _tesseract_disponible():
        return ""

    try:
        image = Image.open(io.BytesIO(contenu))
        return pytesseract.image_to_string(image, lang="fra+eng")
    except Exception as exc:
        logger.warning("OCR image échoué : %s", exc)
        return ""


def _texte_pdf(contenu: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""

    try:
        reader = PdfReader(io.BytesIO(contenu))
        parties: list[str] = []
        for page in reader.pages[:3]:
            texte = page.extract_text() or ""
            if texte.strip():
                parties.append(texte)
        return "\n".join(parties)
    except Exception as exc:
        logger.warning("Extraction PDF échouée : %s", exc)
        return ""


def _ocr_pdf_scan(contenu: bytes) -> str:
    if not _tesseract_disponible():
        return ""
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
    except ImportError:
        return ""

    try:
        images = convert_from_bytes(contenu, first_page=1, last_page=1, dpi=200)
        if not images:
            return ""
        return pytesseract.image_to_string(images[0], lang="fra+eng")
    except Exception as exc:
        logger.warning("OCR PDF scan échoué : %s", exc)
        return ""


def extraire_texte(contenu: bytes, nom_fichier: str) -> tuple[str, str]:
    """Retourne (texte, méthode utilisée)."""
    ext = (nom_fichier.rsplit(".", 1)[-1] if "." in nom_fichier else "").lower()

    if ext == "pdf":
        texte = _texte_pdf(contenu)
        if len(texte.strip()) >= 30:
            return texte, "pdf_texte"
        ocr = _ocr_pdf_scan(contenu)
        if ocr.strip():
            return ocr, "pdf_ocr"
        return texte, "pdf_texte"

    if ext in ("jpg", "jpeg", "png"):
        ocr = _ocr_image(contenu)
        return ocr, "image_ocr" if ocr.strip() else "image_sans_ocr"

    return "", "non_supporte"


def _premiere_ligne_significative(lignes: list[str]) -> str | None:
    for ligne in lignes:
        ligne = ligne.strip()
        if len(ligne) >= 3 and not ligne.isdigit():
            return ligne[:120]
    return None


def _extraire_champs(texte: str) -> dict[str, str | None]:
    lignes = [ln.strip() for ln in texte.splitlines() if ln.strip()]
    texte_plat = " ".join(lignes)

    reference = None
    for pattern in REF_PATTERNS:
        match = pattern.search(texte_plat)
        if match:
            reference = match.group(1).strip()[:80]
            break

    objet = None
    for pattern in OBJET_PATTERNS:
        match = pattern.search(texte_plat)
        if match:
            objet = match.group(1).strip().split("  ")[0][:200]
            break
    if not objet and len(lignes) >= 2:
        for ligne in lignes[1:6]:
            if len(ligne) > 15 and "objet" not in ligne.lower():
                objet = ligne[:200]
                break

    expediteur = None
    for pattern in EXPEDITEUR_PATTERNS:
        match = pattern.search(texte_plat)
        if match:
            expediteur = match.group(1).strip().split(",")[0][:120]
            break
    if not expediteur:
        expediteur = _premiere_ligne_significative(lignes[:8])

    return {
        "expediteur": expediteur,
        "reference_document": reference,
        "objet": objet,
    }


def analyser_document(contenu: bytes, nom_fichier: str) -> dict[str, Any]:
    texte, methode = extraire_texte(contenu, nom_fichier)
    champs = _extraire_champs(texte) if texte.strip() else {}

    ocr_disponible = _tesseract_disponible()
    avertissement = None
    if methode == "image_sans_ocr" and not ocr_disponible:
        avertissement = (
            "OCR images indisponible (Tesseract non installé sur le serveur)."
        )
    elif methode == "pdf_texte" and len(texte.strip()) < 30:
        avertissement = (
            "Peu de texte extrait — document peut-être scanné sans OCR serveur."
        )

    return {
        "texte_brut": texte[:4000],
        "methode": methode,
        "ocr_disponible": ocr_disponible,
        "avertissement": avertissement,
        "suggestions": champs,
        "confiance": "haute" if any(champs.values()) and len(texte) > 50 else "basse",
    }
