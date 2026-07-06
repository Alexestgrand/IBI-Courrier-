"""Services de gestion des utilisateurs."""

from sqlalchemy.orm import Session

from app.auth import hasher_mot_de_passe
from app.constants import ROLES_VALIDES
from app.models import User
from app.services import enregistrer_audit


def _sans_mot_de_passe(user: User) -> dict:
    return {
        "id": user.id,
        "nom": user.nom,
        "prenom": user.prenom,
        "email": user.email,
        "role": user.role,
        "actif": user.actif,
        "derniere_connexion": user.derniere_connexion,
    }


def _compter_admins_actifs(db: Session) -> int:
    return (
        db.query(User)
        .filter(User.role == "admin", User.actif.is_(True))
        .count()
    )


def _verifier_garde_fous_admin(
    db: Session,
    cible: User,
    admin: User,
    *,
    nouveau_role: str | None = None,
    desactivation: bool = False,
) -> None:
    if desactivation and cible.id == admin.id:
        raise ValueError("Vous ne pouvez pas vous désactiver vous-même.")

    if nouveau_role is not None and cible.id == admin.id and nouveau_role != "admin":
        raise ValueError("Vous ne pouvez pas retirer votre propre rôle admin.")

    role_final = nouveau_role if nouveau_role is not None else cible.role
    retire_admin = cible.role == "admin" and role_final != "admin"

    if cible.role == "admin" and cible.actif and (desactivation or retire_admin):
        if _compter_admins_actifs(db) <= 1:
            raise ValueError(
                "Impossible de désactiver ou modifier le dernier administrateur actif."
            )


def lister_utilisateurs(
    db: Session,
    recherche: str | None = None,
    role: str | None = None,
) -> list[dict]:
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if recherche:
        terme = f"%{recherche.strip()}%"
        query = query.filter(
            User.nom.ilike(terme)
            | User.prenom.ilike(terme)
            | User.email.ilike(terme)
        )
    users = query.order_by(User.nom, User.prenom).all()
    return [_sans_mot_de_passe(u) for u in users]


def creer_utilisateur(
    db: Session,
    admin: User,
    nom: str,
    prenom: str,
    email: str,
    role: str,
    mot_de_passe: str,
    actif: bool = True,
) -> User:
    if role not in ROLES_VALIDES:
        raise ValueError("Rôle invalide.")
    if not mot_de_passe.strip():
        raise ValueError("Le mot de passe est obligatoire.")

    email = email.strip().lower()
    if db.query(User).filter(User.email.ilike(email)).first():
        raise ValueError("Cet e-mail est déjà utilisé.")

    user = User(
        nom=nom.strip(),
        prenom=prenom.strip(),
        email=email,
        role=role,
        mot_de_passe=hasher_mot_de_passe(mot_de_passe),
        actif=actif,
    )
    db.add(user)
    enregistrer_audit(db, admin.id, "creation_utilisateur", email, "users")
    db.commit()
    db.refresh(user)
    return user


def mettre_a_jour_utilisateur(
    db: Session,
    admin: User,
    user_id: int,
    nom: str | None = None,
    prenom: str | None = None,
    email: str | None = None,
    role: str | None = None,
    actif: bool | None = None,
) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise ValueError("Utilisateur introuvable.")

    desactivation = actif is False and user.actif
    if role is not None and role not in ROLES_VALIDES:
        raise ValueError("Rôle invalide.")

    _verifier_garde_fous_admin(
        db, user, admin, nouveau_role=role, desactivation=desactivation
    )

    if email is not None:
        email = email.strip().lower()
        existant = db.query(User).filter(User.email.ilike(email), User.id != user_id).first()
        if existant:
            raise ValueError("Cet e-mail est déjà utilisé.")
        user.email = email
    if nom is not None:
        user.nom = nom.strip()
    if prenom is not None:
        user.prenom = prenom.strip()
    if role is not None:
        user.role = role
    if actif is not None:
        user.actif = actif

    enregistrer_audit(
        db, admin.id, "modification_utilisateur", f"Utilisateur {user.email}", "users"
    )
    db.commit()
    db.refresh(user)
    return user


def reinitialiser_mot_de_passe(
    db: Session,
    admin: User,
    user_id: int,
    mot_de_passe: str,
) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise ValueError("Utilisateur introuvable.")

    nouveau = mot_de_passe.strip()
    if len(nouveau) < 6:
        raise ValueError("Le mot de passe doit contenir au moins 6 caractères.")

    user.mot_de_passe = hasher_mot_de_passe(nouveau)
    user.must_change_password = True
    enregistrer_audit(
        db, admin.id, "reinitialisation_mot_de_passe", f"Utilisateur {user.email}", "users"
    )
    db.commit()
