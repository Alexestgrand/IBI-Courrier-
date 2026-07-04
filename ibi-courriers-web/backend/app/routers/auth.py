"""Routes d'authentification."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import (
    creer_token_acces,
    obtenir_utilisateur_courant,
    verifier_mot_de_passe,
)
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, TokenResponse, UserResponse
from app.services import enregistrer_audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = (
        db.query(User)
        .filter(User.email.ilike(data.email.strip()), User.actif.is_(True))
        .first()
    )
    if user is None or not verifier_mot_de_passe(data.mot_de_passe, user.mot_de_passe):
        enregistrer_audit(
            db,
            user.id if user else None,
            "connexion_echouee",
            f"Tentative pour {data.email}",
            "auth",
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects.",
        )

    user.derniere_connexion = datetime.now(timezone.utc)
    enregistrer_audit(db, user.id, "connexion_reussie", data.email, "auth")
    db.commit()

    token = creer_token_acces(user.id, user.role)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(obtenir_utilisateur_courant)) -> User:
    return user
