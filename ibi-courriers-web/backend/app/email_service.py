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


def envoyer_email_test(destinataire: str) -> None:
    """Envoie un e-mail de test ; lève une exception en cas d'échec."""
    if not settings.smtp_enabled:
        raise ValueError("SMTP désactivé. Activez SMTP_ENABLED dans la configuration.")

    msg = MIMEMultipart()
    msg["From"] = settings.smtp_from
    msg["To"] = destinataire
    msg["Subject"] = "[IBI Courriers] E-mail de test"
    msg.attach(
        MIMEText(
            "Ceci est un e-mail de test envoyé depuis IBI Courriers Web.\n"
            "Si vous recevez ce message, la configuration SMTP est correcte.",
            "plain",
            "utf-8",
        )
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.sendmail(settings.smtp_from, [destinataire], msg.as_string())


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


def notifier_echec_sauvegarde(message: str) -> None:
    """Alerte les administrateurs configurés en cas d'échec de sauvegarde."""
    destinataires = settings.notify_emails_list
    if not destinataires:
        raise ValueError(
            "NOTIFY_EMAILS non configuré — impossible d'envoyer l'alerte sauvegarde."
        )
    if not settings.smtp_enabled:
        raise ValueError("SMTP désactivé — activez SMTP_ENABLED pour les alertes.")

    sujet = "[IBI Courriers] Échec de sauvegarde"
    corps = (
        f"La sauvegarde automatique IBI Courriers a échoué.\n\n"
        f"Détail : {message}\n\n"
        f"Vérifiez les logs sur le serveur (logs/backup.log) et lancez un test manuel :\n"
        f"  ./scripts/backup.sh\n"
    )
    _envoyer(destinataires, sujet, corps)


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
