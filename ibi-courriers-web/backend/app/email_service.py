"""Notifications e-mail (SMTP)."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.config import settings
from app.constants import service_pour_role
from app.models import Courrier, User

logger = logging.getLogger(__name__)


def _envoyer(destinataires: list[str], sujet: str, corps: str) -> None:
    if not settings.smtp_enabled or not destinataires:
        return

    msg = MIMEMultipart()
    msg["From"] = settings.smtp_from
    msg["To"] = ", ".join(destinataires)
    msg["Subject"] = sujet
    msg.attach(MIMEText(corps, "plain", "utf-8"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.sendmail(settings.smtp_from, destinataires, msg.as_string())
    except Exception as exc:
        logger.warning("Échec envoi e-mail : %s", exc)


def destinataires_pour_service(db: Session, service: str) -> list[str]:
    emails: list[str] = []
    for user in db.query(User).filter(User.actif.is_(True)).all():
        if user.role in ("admin", "dg"):
            emails.append(user.email)
            continue
        if service_pour_role(user.role) == service:
            emails.append(user.email)

    extras = [e.strip() for e in settings.notify_emails_list if e.strip()]
    return list(dict.fromkeys(emails + extras))


def notifier_courrier_entrant(db: Session, courrier: Courrier) -> None:
    if not courrier.service_destinataire:
        return

    destinataires = destinataires_pour_service(db, courrier.service_destinataire)
    sujet = f"[IBI Courriers] Nouveau courrier {courrier.numero}"
    corps = (
        f"Un nouveau courrier entrant a été enregistré.\n\n"
        f"Numéro : {courrier.numero}\n"
        f"Objet : {courrier.objet}\n"
        f"Expéditeur : {courrier.expediteur}\n"
        f"Service destinataire : {courrier.service_destinataire}\n"
        f"Urgence : {courrier.urgence}\n"
    )
    _envoyer(destinataires, sujet, corps)
