"""Amélioration extraction OCR pour scans de qualité moyenne."""

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
    re.compile(r"affaire\s*[:\-]\s*(.+)", re.IGNORECASE),
]

EXPEDITEUR_PATTERNS = [
    re.compile(r"(?:de|exp[ée]diteur|sender|émetteur)\s*[:\-]\s*(.+)", re.IGNORECASE),
    re.compile(r"(?:monsieur|madame|m\.|mme\.?|dr\.?)\s+(.+)", re.IGNORECASE),
]

ORGANISME_PATTERNS = [
    re.compile(r"\b(SA|SARL|SAS|S\.A\.|S\.A\.R\.L\.)\b", re.IGNORECASE),
    re.compile(
        r"\b(ministère|direction générale|banque|société|groupe|office|ordre)\b",
        re.IGNORECASE,
    ),
]

LIGNE_A_IGNORER = re.compile(
    r"^(page\s+\d+|tél|tel|fax|e-?mail|www\.|http|bp\s+\d+|"
    r"\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|"
    r"^\d+$|abidjan|plateau|cocody|treichville)",
    re.IGNORECASE,
)


def _tesseract_disponible() -> bool:
    return shutil.which("tesseract") is not None


def _pretraiter_image(image):
    from PIL import ImageEnhance, ImageOps

    image = ImageOps.exif_transpose(image)
    image = image.convert("L")
    image = ImageEnhance.Contrast(image).enhance(1.6)
    image = ImageEnhance.Sharpness(image).enhance(1.3)
    return image


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
        image = _pretraiter_image(image)
        config = "--psm 6 --oem 3"
        return pytesseract.image_to_string(image, lang="fra+eng", config=config)
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
        images = convert_from_bytes(contenu, first_page=1, last_page=2, dpi=300)
        textes: list[str] = []
        config = "--psm 6 --oem 3"
        for image in images:
            image = _pretraiter_image(image)
            textes.append(pytesseract.image_to_string(image, lang="fra+eng", config=config))
        return "\n".join(textes)
    except Exception as exc:
        logger.warning("OCR PDF scan échoué : %s", exc)
        return ""


def extraire_texte(contenu: bytes, nom_fichier: str) -> tuple[str, str]:
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


def _lignes_utiles(texte: str) -> list[str]:
    lignes: list[str] = []
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        if len(ligne) < 3:
            continue
        if LIGNE_A_IGNORER.search(ligne):
            continue
        lignes.append(ligne)
    return lignes


def _score_ligne_expediteur(ligne: str) -> int:
    score = min(len(ligne), 80)
    if ORGANISME_PATTERNS[0].search(ligne):
        score += 40
    if ORGANISME_PATTERNS[1].search(ligne):
        score += 30
    if ligne.isupper() and len(ligne) > 6:
        score += 20
    if re.search(r"\d{5,}", ligne):
        score -= 30
    return score


def _deviner_expediteur(lignes: list[str]) -> str | None:
    for pattern in EXPEDITEUR_PATTERNS:
        for ligne in lignes[:15]:
            match = pattern.search(ligne)
            if match:
                candidat = match.group(1).strip().split(",")[0][:120]
                if len(candidat) >= 3:
                    return candidat

    candidats = sorted(
        ((ln, _score_ligne_expediteur(ln)) for ln in lignes[:12]),
        key=lambda x: x[1],
        reverse=True,
    )
    for ligne, score in candidats:
        if score >= 25 and len(ligne) >= 4:
            return ligne[:120]
    return lignes[0][:120] if lignes else None


def _extraire_champs(texte: str) -> dict[str, str | None]:
    lignes = _lignes_utiles(texte)
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
    if not objet:
        for ligne in lignes[1:8]:
            if len(ligne) > 20 and "objet" not in ligne.lower():
                objet = ligne[:200]
                break

    expediteur = _deviner_expediteur(lignes)

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
    elif methode in ("pdf_ocr", "image_ocr") and not any(champs.values()):
        avertissement = (
            "Texte détecté mais peu de champs reconnus — vérifiez et complétez manuellement."
        )
    elif methode == "pdf_texte" and len(texte.strip()) < 30:
        avertissement = (
            "Peu de texte extrait — document peut-être scanné sans OCR serveur."
        )

    confiance = "basse"
    if any(champs.values()) and len(texte) > 80:
        confiance = "haute"
    elif any(champs.values()):
        confiance = "moyenne"

    return {
        "texte_brut": texte[:4000],
        "methode": methode,
        "ocr_disponible": ocr_disponible,
        "avertissement": avertissement,
        "suggestions": champs,
        "confiance": confiance,
    }
