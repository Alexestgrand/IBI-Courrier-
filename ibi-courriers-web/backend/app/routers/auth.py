"""Routes d'authentification."""

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.auth import (
    creer_token_acces,
    hasher_mot_de_passe,
    obtenir_utilisateur_courant,
    revoquer_sessions_utilisateur,
    verifier_mot_de_passe,
)
from app.auth_cookies import definir_cookie_session, effacer_cookie_session
from app.uploads import valider_contenu_png
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, LoginResponse, UserResponse, ChangePasswordRequest
from app.rate_limit import verifier_rate_limit_login
from app.services import (
    enregistrer_audit,
    enregistrer_signature_utilisateur,
    supprimer_signature_utilisateur,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        nom=user.nom,
        prenom=user.prenom,
        email=user.email,
        role=user.role,
        actif=user.actif,
        must_change_password=user.must_change_password,
        a_signature=bool(user.chemin_signature),
        derniere_connexion=user.derniere_connexion,
    )


def _reponse_avec_session(user: User, message: str) -> JSONResponse:
    token = creer_token_acces(user.id, user.role, user.token_version or 0)
    response = JSONResponse(
        content=LoginResponse(
            must_change_password=user.must_change_password,
            message=message,
        ).model_dump()
    )
    definir_cookie_session(response, token)
    return response


@router.post("/login", response_model=LoginResponse)
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> JSONResponse:
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

    return _reponse_avec_session(user, "Connecté.")


@router.post("/logout")
def logout(
    user: User = Depends(obtenir_utilisateur_courant),
    db: Session = Depends(get_db),
) -> JSONResponse:
    revoquer_sessions_utilisateur(user)
    enregistrer_audit(db, user.id, "deconnexion", user.email, "auth")
    db.commit()
    response = JSONResponse(content={"message": "Déconnecté."})
    effacer_cookie_session(response)
    return response


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(obtenir_utilisateur_courant)) -> UserResponse:
    return _user_response(user)


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(obtenir_utilisateur_courant),
) -> JSONResponse:
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
    revoquer_sessions_utilisateur(user)
    enregistrer_audit(db, user.id, "changement_mot_de_passe", user.email, "auth")
    db.commit()
    db.refresh(user)
    return _reponse_avec_session(user, "Mot de passe modifié.")


@router.post("/signature")
async def post_signature(
    fichier: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(obtenir_utilisateur_courant),
) -> dict[str, str]:
    contenu = await fichier.read()
    try:
        valider_contenu_png(contenu)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    enregistrer_signature_utilisateur(db, user, contenu)
    enregistrer_audit(db, user.id, "signature_enregistree", user.email, "auth")
    return {"message": "Signature enregistrée."}


@router.get("/signature")
def get_signature(user: User = Depends(obtenir_utilisateur_courant)):
    if not user.chemin_signature or not os.path.isfile(user.chemin_signature):
        raise HTTPException(status_code=404, detail="Aucune signature enregistrée.")
    return FileResponse(user.chemin_signature, media_type="image/png")


@router.delete("/signature")
def delete_signature(
    db: Session = Depends(get_db),
    user: User = Depends(obtenir_utilisateur_courant),
) -> dict[str, str]:
    supprimer_signature_utilisateur(db, user)
    enregistrer_audit(db, user.id, "signature_supprimee", user.email, "auth")
    return {"message": "Signature supprimée."}
