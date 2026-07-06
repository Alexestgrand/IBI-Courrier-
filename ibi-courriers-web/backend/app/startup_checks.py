"""Validations bloquantes au démarrage en production."""

import logging

from app.config import settings

logger = logging.getLogger(__name__)

_SECRET_KEYS_INTERDITS = frozenset(
    {
        "changez-moi-en-production",
        "changez-moi-en-production-avec-une-cle-longue",
        "test-secret-key",
        "ci-test-key",
    }
)


def valider_configuration() -> None:
    env = settings.environment.lower()
    if env not in ("production", "prod"):
        return

    erreurs: list[str] = []

    if (
        not settings.secret_key
        or settings.secret_key in _SECRET_KEYS_INTERDITS
        or len(settings.secret_key) < 32
    ):
        erreurs.append(
            "SECRET_KEY invalide en production (min. 32 caractères, valeur unique requise)."
        )

    if "ibi_secret" in settings.database_url:
        erreurs.append(
            "DATABASE_URL utilise le mot de passe par défaut « ibi_secret » en production."
        )

    if erreurs:
        for msg in erreurs:
            logger.critical(msg)
        raise RuntimeError(
            "Configuration de production invalide : " + " | ".join(erreurs)
        )
