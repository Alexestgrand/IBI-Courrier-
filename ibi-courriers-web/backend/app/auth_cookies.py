"""Cookie de session httpOnly pour le JWT."""

from fastapi import Response

from app.config import settings

COOKIE_PATH = "/api"


def _cookie_secure() -> bool:
    if settings.cookie_secure is not None:
        return settings.cookie_secure
    return settings.environment.lower() in ("production", "prod")


def definir_cookie_session(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path=COOKIE_PATH,
    )


def effacer_cookie_session(response: Response) -> None:
    response.delete_cookie(
        key=settings.cookie_name,
        path=COOKIE_PATH,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
    )
