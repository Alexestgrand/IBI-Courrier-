"""Tests validation des uploads."""

import pytest

from app.uploads import valider_contenu_upload


def test_pdf_valide():
    contenu = b"%PDF-1.4 contenu test"
    ext = valider_contenu_upload(contenu, "document.pdf")
    assert ext == ".pdf"


def test_extension_ne_correspond_pas_au_contenu():
    with pytest.raises(ValueError, match="ne correspond pas"):
        valider_contenu_upload(b"%PDF-1.4 fake", "image.png")


def test_fichier_trop_volumineux(monkeypatch):
    import app.uploads as uploads_mod

    monkeypatch.setattr(uploads_mod, "MAX_UPLOAD_BYTES", 100)
    contenu = b"%PDF-1.4" + b"x" * 200
    with pytest.raises(ValueError, match="trop volumineux"):
        valider_contenu_upload(contenu, "gros.pdf")
