"""Rate limiting simple en mémoire (login, OCR)."""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

from app.config import settings
from app.http_utils import obtenir_ip_client
from app.models import User

_MAX_TENTATIVES_LOGIN = 10
_FENETRE_LOGIN_SEC = 60
_compteurs: dict[str, list[float]] = defaultdict(list)


def _verifier_rate_limit(cle: str, max_tentatives: int, fenetre_sec: int) -> None:
    maintenant = time.time()
    fenetre = _compteurs[cle]
    fenetre[:] = [t for t in fenetre if maintenant - t < fenetre_sec]

    if len(fenetre) >= max_tentatives:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de requêtes. Réessayez dans quelques instants.",
        )

    fenetre.append(maintenant)


def verifier_rate_limit_login(request: Request) -> None:
    ip = obtenir_ip_client(request)
    _verifier_rate_limit(f"login:{ip}", _MAX_TENTATIVES_LOGIN, _FENETRE_LOGIN_SEC)


def verifier_rate_limit_ocr(request: Request, user: User) -> None:
    ip = obtenir_ip_client(request)
    cle = f"ocr:{user.id}:{ip}"
    _verifier_rate_limit(
        cle,
        settings.rate_limit_ocr_max,
        settings.rate_limit_ocr_window_sec,
    )
