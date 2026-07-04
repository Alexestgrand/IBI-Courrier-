"""Constantes métier (workflow, rôles, libellés)."""

STATUTS = ("en_attente", "transmis", "valide", "rejete", "archive")

LIBELLES_STATUT = {
    "en_attente": "En attente",
    "transmis": "Transmis",
    "valide": "Validé",
    "rejete": "Rejeté",
    "archive": "Archivé",
}

TRANSITIONS_VALIDES = {
    "en_attente": ("transmis",),
    "transmis": ("valide", "rejete"),
    "valide": ("archive",),
    "rejete": ("archive",),
    "archive": (),
}

TRANSITIONS_PAR_ROLE = {
    "reception": (("en_attente", "transmis"),),
    "dg": (
        ("transmis", "valide"),
        ("transmis", "rejete"),
        ("valide", "archive"),
        ("rejete", "archive"),
    ),
    "admin": "toutes",
    "comptabilite": (),
    "marche": (),
    "achat": (),
}

ROLES_VALIDES = (
    "admin",
    "dg",
    "reception",
    "comptabilite",
    "marche",
    "achat",
)

URGENCES_VALIDES = ("normal", "urgent", "très urgent")

EXTENSIONS_AUTORISEES = {".pdf", ".jpg", ".jpeg", ".png", ".docx"}

ENTITES_DEFAUT = (
    "IBI",
    "Thabor",
    "Mamel",
    "N'kafu",
    "Lemetier",
    "BAYI",
    "comm'eve",
    "Calao",
)

SERVICES_DEFAUT = (
    "Direction",
    "Comptabilité",
    "Service Marché",
    "Facturation",
    "DAF",
    "Service Audit",
    "Service Informatique",
)
