"""Rate limiting simple en mémoire (login)."""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

_MAX_TENTATIVES = 10
_FENETRE_SEC = 60
_tentatives: dict[str, list[float]] = defaultdict(list)


def verifier_rate_limit_login(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    maintenant = time.time()
    fenetre = _tentatives[ip]
    fenetre[:] = [t for t in fenetre if maintenant - t < _FENETRE_SEC]

    if len(fenetre) >= _MAX_TENTATIVES:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de tentatives. Réessayez dans une minute.",
        )

    fenetre.append(maintenant)
