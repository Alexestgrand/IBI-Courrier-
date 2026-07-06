"""Routes OCR (extraction depuis scans)."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.auth import exiger_session_complete
from app.config import settings
from app.models import User
from app.ocr_service import analyser_document
from app.schemas import OcrExtractionResponse
from app.uploads import lire_upload_valide

router = APIRouter(prefix="/ocr", tags=["ocr"])

EXTENSIONS_OCR = {".pdf", ".jpg", ".jpeg", ".png"}


@router.post("/extract", response_model=OcrExtractionResponse)
async def post_ocr_extract(
    fichier: UploadFile = File(...),
    _: User = Depends(exiger_session_complete),
) -> dict:
    if not settings.ocr_enabled:
        raise HTTPException(status_code=503, detail="OCR désactivé sur ce serveur.")

    try:
        contenu, _ = await lire_upload_valide(fichier, EXTENSIONS_OCR)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if len(contenu) < 100:
        raise HTTPException(status_code=400, detail="Fichier vide ou invalide.")

    return analyser_document(contenu, fichier.filename)
