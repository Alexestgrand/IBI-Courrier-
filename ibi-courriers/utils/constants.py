"""Constantes métier partagées (statuts, urgences, libellés, couleurs)."""

# Note cahier des charges : le statut « Traité » correspond à « Validé » (valide).
# Ancienne valeur DB « traite » migrée vers « valide » au démarrage.
STATUTS: tuple[str, ...] = (
    "en_attente",
    "transmis",
    "valide",
    "rejete",
    "archive",
)

LIBELLES_STATUT: dict[str, str] = {
    "en_attente": "En attente",
    "transmis": "Transmis",
    "valide": "Validé",
    "rejete": "Rejeté",
    "archive": "Archivé",
}

# Alias doc-only (cahier des charges) — ne pas persister en base.
ALIAS_STATUT_CAHIER: dict[str, str] = {"traite": "valide"}

COULEURS_STATUT: dict[str, str] = {
    "en_attente": "#F1C40F",
    "transmis": "#3498DB",
    "valide": "#6BCB77",
    "rejete": "#FF6B6B",
    "archive": "#95A5A6",
}

LIBELLES_URGENCE: dict[str, str] = {
    "normal": "Normal",
    "urgent": "Urgent",
    "très urgent": "Très urgent",
}

COULEURS_URGENCE: dict[str, str] = {
    "normal": "#95A5A6",
    "urgent": "#E67E22",
    "très urgent": "#E74C3C",
}

# Transitions valides dans le workflow
TRANSITIONS_VALIDES: dict[str, tuple[str, ...]] = {
    "en_attente": ("transmis",),
    "transmis": ("valide", "rejete"),
    "valide": ("archive",),
    "rejete": ("archive",),
    "archive": (),
}

TRANSITIONS_PAR_ROLE: dict[str, tuple[tuple[str, str], ...] | str] = {
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

FILTRES_STATUT: dict[str, str | None] = {
    "Tous": None,
    "En attente": "en_attente",
    "Transmis": "transmis",
    "Validé": "valide",
    "Rejeté": "rejete",
    "Archivé": "archive",
}

URGENCES_UI: dict[str, str] = {
    "Normal": "normal",
    "Urgent": "urgent",
    "Très urgent": "très urgent",
}

COULEURS_TYPE: dict[str, str] = {
    "entrant": "#3498DB",
    "sortant": "#9B59B6",
}

LIBELLES_TYPE: dict[str, str] = {
    "entrant": "Entrant",
    "sortant": "Sortant",
}

FILTRES_STATUT_RECHERCHE = FILTRES_STATUT

FILTRES_TYPE_RECHERCHE: dict[str, str | None] = {
    "Tous": None,
    "Entrant": "entrant",
    "Sortant": "sortant",
}

FILTRES_URGENCE_RECHERCHE: dict[str, str | None] = {
    "Tous": None,
    "Normal": "normal",
    "Urgent": "urgent",
    "Très urgent": "très urgent",
}

COULEURS_ROLE: dict[str, str] = {
    "admin": "#E74C3C",
    "dg": "#9B59B6",
    "reception": "#3498DB",
    "comptabilite": "#6BCB77",
    "marche": "#E67E22",
    "achat": "#F1C40F",
}

LIBELLES_ROLE_UI: dict[str, str] = {
    "admin": "Admin",
    "dg": "DG",
    "reception": "Réception",
    "comptabilite": "Comptabilité",
    "marche": "Marché",
    "achat": "Achat",
}

FILTRES_ROLE_UTILISATEURS: dict[str, str | None] = {
    "Tous": None,
    "Admin": "admin",
    "DG": "dg",
    "Réception": "reception",
    "Comptabilité": "comptabilite",
    "Marché": "marche",
    "Achat": "achat",
}

ROLES_VALIDES: tuple[str, ...] = (
    "admin",
    "dg",
    "reception",
    "comptabilite",
    "marche",
    "achat",
)

FILTRES_MODULE_AUDIT: dict[str, str | None] = {
    "Tous": None,
    "Connexion": "auth",
    "Courriers": "courriers",
    "Recherche": "recherche",
    "Utilisateurs": "users",
    "Système": "systeme",
}
