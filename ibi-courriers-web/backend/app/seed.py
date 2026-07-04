"""Initialisation des données par défaut."""

from sqlalchemy.orm import Session

from app.auth import hasher_mot_de_passe
from app.constants import ENTITES_DEFAUT, SERVICES_DEFAUT
from app.models import Entite, Service, User
from app.services import _code_entite


def initialiser_donnees(db: Session) -> None:
    admin = db.query(User).filter(User.email == "admin@ibi.local").first()
    if admin is not None:
        admin.email = "admin@ibi.ci"

    if db.query(User).count() == 0:
        db.add(
            User(
                nom="Admin",
                prenom="IBI",
                email="admin@ibi.ci",
                mot_de_passe=hasher_mot_de_passe("admin123"),
                role="admin",
                actif=True,
            )
        )

    for nom in ENTITES_DEFAUT:
        if db.query(Entite).filter(Entite.nom == nom).first() is None:
            db.add(Entite(nom=nom, code=_code_entite(nom), actif=True))

    for nom in SERVICES_DEFAUT:
        if db.query(Service).filter(Service.nom == nom).first() is None:
            db.add(Service(nom=nom, actif=True))

    db.commit()
