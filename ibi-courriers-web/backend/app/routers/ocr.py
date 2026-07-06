"""Routes OCR (extraction depuis scans)."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.auth import obtenir_utilisateur_courant
from app.config import settings
from app.models import User
from app.ocr_service import analyser_document
from app.schemas import OcrExtractionResponse

router = APIRouter(prefix="/ocr", tags=["ocr"])

EXTENSIONS_OCR = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_OCR_BYTES = 15 * 1024 * 1024


@router.post("/extract", response_model=OcrExtractionResponse)
async def post_ocr_extract(
    fichier: UploadFile = File(...),
    _: User = Depends(obtenir_utilisateur_courant),
) -> dict:
    if not settings.ocr_enabled:
        raise HTTPException(status_code=503, detail="OCR désactivé sur ce serveur.")

    if not fichier.filename:
        raise HTTPException(status_code=400, detail="Fichier requis.")

    ext = "." + fichier.filename.rsplit(".", 1)[-1].lower() if "." in fichier.filename else ""
    if ext not in EXTENSIONS_OCR:
        raise HTTPException(
            status_code=400,
            detail="Formats acceptés : PDF, JPG, PNG.",
        )

    contenu = await fichier.read()
    if len(contenu) > MAX_OCR_BYTES:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 15 Mo).")
    if len(contenu) < 100:
        raise HTTPException(status_code=400, detail="Fichier vide ou invalide.")

    return analyser_document(contenu, fichier.filename)
