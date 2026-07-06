"""Routes d'authentification."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth import (
    creer_token_acces,
    obtenir_utilisateur_courant,
    verifier_mot_de_passe,
)
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, TokenResponse, UserResponse, ChangePasswordRequest
from app.rate_limit import verifier_rate_limit_login
from app.services import enregistrer_audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    verifier_rate_limit_login(request)
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
    return TokenResponse(
        access_token=token,
        must_change_password=user.must_change_password,
    )


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(obtenir_utilisateur_courant)) -> User:
    return user


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(obtenir_utilisateur_courant),
) -> dict[str, str]:
    from app.auth import hasher_mot_de_passe

    if not verifier_mot_de_passe(data.ancien_mot_de_passe, user.mot_de_passe):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ancien mot de passe incorrect.",
        )
    if len(data.nouveau_mot_de_passe) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nouveau mot de passe doit contenir au moins 6 caractères.",
        )
    user.mot_de_passe = hasher_mot_de_passe(data.nouveau_mot_de_passe)
    user.must_change_password = False
    enregistrer_audit(db, user.id, "changement_mot_de_passe", user.email, "auth")
    db.commit()
    return {"message": "Mot de passe modifié."}
