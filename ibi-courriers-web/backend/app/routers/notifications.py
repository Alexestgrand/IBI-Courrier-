"""Routes notifications in-app."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import obtenir_utilisateur_courant
from app.database import get_db
from app.models import User
from app.schemas import NotificationResponse, UnreadCountResponse
from app.services_notifications import (
    compter_non_lues,
    lister_notifications,
    marquer_lue,
    marquer_toutes_lues,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
def get_notifications(
    non_lues: bool = False,
    limit: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(obtenir_utilisateur_courant),
):
    rows = lister_notifications(db, user.id, non_lues_seulement=non_lues, limit=limit)
    return rows


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    user: User = Depends(obtenir_utilisateur_courant),
):
    return {"count": compter_non_lues(db, user.id)}


@router.patch("/{notification_id}/read")
def patch_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(obtenir_utilisateur_courant),
):
    if not marquer_lue(db, user.id, notification_id):
        raise HTTPException(status_code=404, detail="Notification introuvable.")
    db.commit()
    return {"message": "Notification marquée comme lue."}


@router.post("/read-all")
def post_read_all(
    db: Session = Depends(get_db),
    user: User = Depends(obtenir_utilisateur_courant),
):
    count = marquer_toutes_lues(db, user.id)
    db.commit()
    return {"message": f"{count} notification(s) marquée(s) comme lue(s)."}
