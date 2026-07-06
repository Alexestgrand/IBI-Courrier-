"""Tests unitaires des transitions de statut."""

import pytest

from app.services import statuts_possibles, transition_autorisee


@pytest.mark.parametrize(
    "role,ancien,nouveau,attendu",
    [
        ("reception", "en_attente", "transmis", True),
        ("reception", "transmis", "valide", False),
        ("reception", "en_attente", "valide", False),
        ("dg", "transmis", "valide", True),
        ("dg", "transmis", "rejete", True),
        ("dg", "en_attente", "transmis", False),
        ("dg", "valide", "archive", True),
        ("admin", "en_attente", "transmis", True),
        ("admin", "transmis", "valide", True),
        ("admin", "valide", "archive", True),
        ("comptabilite", "en_attente", "transmis", False),
    ],
)
def test_transition_autorisee(role, ancien, nouveau, attendu):
    assert transition_autorisee(role, ancien, nouveau) is attendu


def test_statuts_possibles_reception():
    assert statuts_possibles("reception", "en_attente") == ["transmis"]
    assert statuts_possibles("reception", "transmis") == []


def test_statuts_possibles_dg():
    possibles = statuts_possibles("dg", "transmis")
    assert set(possibles) == {"valide", "rejete"}


def test_statuts_possibles_admin():
    possibles = statuts_possibles("admin", "en_attente")
    assert possibles == ["transmis"]
