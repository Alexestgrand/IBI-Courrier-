"""Contrôle d'accès aux courriers par rôle et service."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Query, Session, joinedload

from app.constants import service_pour_role
from app.models import Courrier, PieceJointe, User

ROLES_ACCES_GLOBAL = frozenset({"admin", "dg", "reception"})
ROLES_SUPPRESSION_GLOBALE = frozenset({"admin", "dg"})
STATUTS_SUPPRIMABLES_CREATEUR = frozenset({"en_attente", "transmis"})


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


def peut_supprimer_courrier(user: User, courrier: Courrier) -> bool:
    if user.role in ROLES_SUPPRESSION_GLOBALE:
        return True
    if courrier.created_by != user.id:
        return False
    return courrier.statut in STATUTS_SUPPRIMABLES_CREATEUR


def verifier_suppression_courrier(user: User, courrier: Courrier) -> None:
    verifier_acces_courrier(user, courrier)
    if peut_supprimer_courrier(user, courrier):
        return
    if courrier.created_by != user.id:
        detail = "Vous ne pouvez supprimer que les courriers que vous avez créés."
    else:
        detail = (
            "Ce courrier ne peut plus être supprimé (statut avancé). "
            "Contactez la direction ou l'administrateur."
        )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
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
