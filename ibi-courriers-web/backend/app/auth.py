"""Authentification JWT et dépendances FastAPI."""

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

security = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"


def hasher_mot_de_passe(mot_de_passe: str) -> str:
    return bcrypt.hashpw(mot_de_passe.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verifier_mot_de_passe(mot_de_passe: str, mot_de_passe_hash: str) -> bool:
    return bcrypt.checkpw(
        mot_de_passe.encode("utf-8"),
        mot_de_passe_hash.encode("utf-8"),
    )


def creer_token_acces(user_id: int, role: str, token_version: int = 0) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "ver": token_version,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def revoquer_sessions_utilisateur(user: User) -> None:
    user.token_version = (user.token_version or 0) + 1


def extraire_token_requete(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    cookie_token = request.cookies.get(settings.cookie_name)
    if cookie_token:
        return cookie_token
    if credentials and credentials.credentials:
        return credentials.credentials
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification requise.",
    )


def obtenir_utilisateur_courant(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = extraire_token_requete(request, credentials)
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub", 0))
        token_version = int(payload.get("ver", 0))
    except (JWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée. Veuillez vous reconnecter.",
        ) from exc

    user = db.query(User).filter(User.id == user_id, User.actif.is_(True)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable.",
        )
    if token_version != (user.token_version or 0):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée. Veuillez vous reconnecter.",
        )
    return user


def exiger_session_complete(user: User = Depends(obtenir_utilisateur_courant)) -> User:
    if user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous devez changer votre mot de passe avant de continuer.",
        )
    return user


def exiger_admin(user: User = Depends(exiger_session_complete)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs.",
        )
    return user


def exiger_dg_ou_admin(user: User = Depends(exiger_session_complete)) -> User:
    if user.role not in ("dg", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé à la direction générale.",
        )
    return user
