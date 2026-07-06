"""Contrôle d'accès aux courriers par rôle et service."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Query, Session, joinedload

from app.constants import service_pour_role
from app.models import Courrier, PieceJointe, User

ROLES_ACCES_GLOBAL = frozenset({"admin", "dg", "reception"})


def peut_acceder_courrier(user: User, courrier: Courrier) -> bool:
    if user.role in ROLES_ACCES_GLOBAL:
        return True
    service_user = service_pour_role(user.role)
    if not service_user:
        return False
    if courrier.type == "entrant":
        return courrier.service_destinataire == service_user
    return courrier.service_emetteur == service_user


def verifier_acces_courrier(user: User, courrier: Courrier) -> None:
    if not peut_acceder_courrier(user, courrier):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à ce courrier.",
        )


def appliquer_filtre_acces_courrier(query: Query, user: User) -> Query:
    if user.role in ROLES_ACCES_GLOBAL:
        return query
    service_user = service_pour_role(user.role)
    if not service_user:
        return query.filter(Courrier.id < 0)
    from sqlalchemy import and_, or_

    return query.filter(
        or_(
            and_(
                Courrier.type == "entrant",
                Courrier.service_destinataire == service_user,
            ),
            and_(
                Courrier.type == "sortant",
                Courrier.service_emetteur == service_user,
            ),
        )
    )


def service_impose_pour_role(role: str) -> str | None:
    if role in ROLES_ACCES_GLOBAL:
        return None
    return service_pour_role(role)


def obtenir_courrier_autorise(
    db: Session,
    courrier_id: int,
    user: User,
    *,
    avec_relations: bool = True,
) -> Courrier:
    query = db.query(Courrier).filter(Courrier.id == courrier_id)
    if avec_relations:
        query = query.options(
            joinedload(Courrier.entite),
            joinedload(Courrier.pieces_jointes),
            joinedload(Courrier.signataire),
        )
    courrier = query.first()
    if courrier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Courrier introuvable.",
        )
    verifier_acces_courrier(user, courrier)
    return courrier


def obtenir_piece_jointe_autorisee(
    db: Session,
    piece_id: int,
    user: User,
) -> PieceJointe:
    pj = (
        db.query(PieceJointe)
        .options(joinedload(PieceJointe.courrier))
        .filter(PieceJointe.id == piece_id)
        .first()
    )
    if pj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier introuvable.",
        )
    if pj.courrier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier introuvable.",
        )
    verifier_acces_courrier(user, pj.courrier)
    return pj
