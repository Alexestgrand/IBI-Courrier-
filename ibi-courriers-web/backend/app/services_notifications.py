"""Notifications in-app (hors e-mail)."""

from sqlalchemy.orm import Session

from app.constants import LIBELLES_STATUT, ROLE_SERVICE_MAP
from app.models import Notification, User

SERVICE_ROLE_MAP = {nom: role for role, nom in ROLE_SERVICE_MAP.items()}


def _ids_par_roles(db: Session, *roles: str) -> list[int]:
    if not roles:
        return []
    rows = (
        db.query(User.id)
        .filter(User.role.in_(roles), User.actif.is_(True))
        .all()
    )
    return [row[0] for row in rows]


def _ids_par_service(db: Session, service: str | None) -> list[int]:
    if not service:
        return []
    role = SERVICE_ROLE_MAP.get(service)
    if not role:
        return []
    return _ids_par_roles(db, role)


def _creer_notifications(
    db: Session,
    user_ids: list[int],
    type_notif: str,
    titre: str,
    message: str,
    courrier_id: int | None = None,
    exclude_user_id: int | None = None,
) -> None:
    for user_id in set(user_ids):
        if exclude_user_id and user_id == exclude_user_id:
            continue
        db.add(
            Notification(
                user_id=user_id,
                type=type_notif,
                titre=titre,
                message=message,
                courrier_id=courrier_id,
            )
        )


def notifier_nouveau_courrier(db: Session, courrier) -> None:
    destinataires: list[int] = []
    if courrier.service_destinataire:
        destinataires.extend(_ids_par_service(db, courrier.service_destinataire))
    if courrier.urgence in ("urgent", "très urgent"):
        destinataires.extend(_ids_par_roles(db, "dg"))

    if not destinataires:
        return

    urgence = f" ({courrier.urgence})" if courrier.urgence != "normal" else ""
    _creer_notifications(
        db,
        destinataires,
        "nouveau_courrier",
        "Nouveau courrier entrant",
        f"{courrier.numero}{urgence} — {courrier.objet[:120]}",
        courrier.id,
        exclude_user_id=courrier.created_by,
    )


def notifier_changement_statut(
    db: Session,
    courrier,
    ancien: str,
    nouveau: str,
    user_id: int,
) -> None:
    libelle = LIBELLES_STATUT.get(nouveau, nouveau)

    if nouveau == "transmis":
        _creer_notifications(
            db,
            _ids_par_roles(db, "dg"),
            "a_valider",
            "Courrier à valider",
            f"{courrier.numero} — {courrier.objet[:120]}",
            courrier.id,
            exclude_user_id=user_id,
        )
        return

    if nouveau in ("valide", "rejete"):
        destinataires = _ids_par_roles(db, "reception")
        if courrier.service_destinataire:
            destinataires.extend(_ids_par_service(db, courrier.service_destinataire))
        _creer_notifications(
            db,
            destinataires,
            f"statut_{nouveau}",
            f"Courrier {libelle.lower()}",
            f"{courrier.numero} — {courrier.objet[:120]}",
            courrier.id,
            exclude_user_id=user_id,
        )


def lister_notifications(
    db: Session,
    user_id: int,
    non_lues_seulement: bool = False,
    limit: int = 30,
) -> list[Notification]:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if non_lues_seulement:
        query = query.filter(Notification.lu.is_(False))
    return query.order_by(Notification.created_at.desc()).limit(limit).all()


def compter_non_lues(db: Session, user_id: int) -> int:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.lu.is_(False))
        .count()
    )


def marquer_lue(db: Session, user_id: int, notification_id: int) -> bool:
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if notif is None:
        return False
    notif.lu = True
    return True


def marquer_toutes_lues(db: Session, user_id: int) -> int:
    rows = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.lu.is_(False))
        .all()
    )
    for row in rows:
        row.lu = True
    return len(rows)
