"""Validation des fichiers uploadés (taille, extension, signature binaire)."""

import os

from fastapi import UploadFile

from app.constants import EXTENSIONS_AUTORISEES

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_SIGNATURE_BYTES = 512 * 1024

_MAGIC_PAR_EXTENSION: dict[str, tuple[bytes, ...]] = {
    ".pdf": (b"%PDF",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".docx": (b"PK\x03\x04",),
}


def _extension_fichier(nom: str) -> str:
    _, ext = os.path.splitext(nom or "")
    return ext.lower()


def _contenu_correspond_extension(contenu: bytes, ext: str) -> bool:
    signatures = _MAGIC_PAR_EXTENSION.get(ext)
    if not signatures:
        return False
    return any(contenu.startswith(sig) for sig in signatures)


def valider_contenu_upload(contenu: bytes, nom_fichier: str) -> str:
    if not contenu:
        raise ValueError("Fichier vide.")
    if len(contenu) > MAX_UPLOAD_BYTES:
        raise ValueError(
            f"Fichier trop volumineux (max {MAX_UPLOAD_BYTES // (1024 * 1024)} Mo)."
        )

    ext = _extension_fichier(nom_fichier)
    if ext not in EXTENSIONS_AUTORISEES:
        raise ValueError(
            f"Extension non autorisée ({ext or 'sans extension'}). "
            f"Formats acceptés : {', '.join(sorted(EXTENSIONS_AUTORISEES))}"
        )
    if not _contenu_correspond_extension(contenu, ext):
        raise ValueError("Le contenu du fichier ne correspond pas à son extension.")
    return ext


def valider_contenu_png(contenu: bytes, max_octets: int = MAX_SIGNATURE_BYTES) -> None:
    if not contenu or len(contenu) < 50:
        raise ValueError("Signature vide ou invalide.")
    if len(contenu) > max_octets:
        raise ValueError(
            f"Signature trop volumineuse (max {max_octets // 1024} Ko)."
        )
    if not contenu.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Le fichier doit être une image PNG.")


async def lire_upload_valide(
    fichier: UploadFile,
    extensions: set[str] | None = None,
) -> tuple[bytes, str]:
    if not fichier.filename:
        raise ValueError("Nom de fichier manquant.")

    ext = _extension_fichier(fichier.filename)
    extensions_autorisees = extensions or EXTENSIONS_AUTORISEES
    if ext not in extensions_autorisees:
        raise ValueError(
            f"Extension non autorisée ({ext}). "
            f"Formats acceptés : {', '.join(sorted(extensions_autorisees))}"
        )

    contenu = await fichier.read()
    if len(contenu) > MAX_UPLOAD_BYTES:
        raise ValueError(
            f"Fichier trop volumineux (max {MAX_UPLOAD_BYTES // (1024 * 1024)} Mo)."
        )
    if not _contenu_correspond_extension(contenu, ext):
        raise ValueError("Le contenu du fichier ne correspond pas à son extension.")
    return contenu, ext
