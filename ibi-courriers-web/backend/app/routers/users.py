"""Routes administration utilisateurs."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import exiger_admin
from app.database import get_db
from app.models import User
from app.schemas import (
    ResetPasswordRequest,
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.services_users import (
    creer_utilisateur,
    lister_utilisateurs,
    mettre_a_jour_utilisateur,
    reinitialiser_mot_de_passe,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
def get_users(
    recherche: str | None = None,
    role: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(exiger_admin),
):
    return lister_utilisateurs(db, recherche, role)


@router.post("", response_model=UserResponse, status_code=201)
def post_user(
    data: UserCreateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(exiger_admin),
):
    try:
        user = creer_utilisateur(
            db,
            admin,
            data.nom,
            data.prenom,
            data.email,
            data.role,
            data.mot_de_passe,
            data.actif,
        )
        return user
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{user_id}", response_model=UserResponse)
def patch_user(
    user_id: int,
    data: UserUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(exiger_admin),
):
    try:
        user = mettre_a_jour_utilisateur(
            db,
            admin,
            user_id,
            data.nom,
            data.prenom,
            data.email,
            data.role,
            data.actif,
        )
        return user
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{user_id}/reset-password")
def post_reset_password(
    user_id: int,
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(exiger_admin),
):
    try:
        mot_de_passe = reinitialiser_mot_de_passe(db, admin, user_id, data.mot_de_passe)
        return {"mot_de_passe": mot_de_passe}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
