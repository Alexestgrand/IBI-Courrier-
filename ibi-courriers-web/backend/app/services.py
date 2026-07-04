"""Services métier."""

import os
import re
import uuid
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.constants import (
    EXTENSIONS_AUTORISEES,
    TRANSITIONS_PAR_ROLE,
    TRANSITIONS_VALIDES,
    URGENCES_VALIDES,
)
from app.models import AuditLog, Courrier, Entite, PieceJointe, Service, StatutLog, User


def _code_entite(nom: str) -> str:
    code = re.sub(r"[^A-Za-z0-9]", "", nom.replace("'", ""))
    return (code[:10] or "ENT").upper()


def enregistrer_audit(
    db: Session,
    user_id: int | None,
    action: str,
    detail: str | None,
    module: str | None,
) -> None:
    db.add(AuditLog(user_id=user_id, action=action, detail=detail, module=module))


def transition_autorisee(role: str, ancien: str, nouveau: str) -> bool:
    regles = TRANSITIONS_PAR_ROLE.get(role, ())
    if regles == "toutes":
        return nouveau in TRANSITIONS_VALIDES.get(ancien, ())
    if not isinstance(regles, tuple):
        return False
    return (ancien, nouveau) in regles


def statuts_possibles(role: str, statut_actuel: str) -> list[str]:
    regles = TRANSITIONS_PAR_ROLE.get(role, ())
    if regles == "toutes":
        return list(TRANSITIONS_VALIDES.get(statut_actuel, ()))
    if not isinstance(regles, tuple) or not regles:
        return []
    return [nouveau for ancien, nouveau in regles if ancien == statut_actuel]


def generer_numero(db: Session, type_courrier: str, code_entite: str) -> str:
    annee = datetime.now().year
    prefixe = "ENT" if type_courrier == "entrant" else "SOR"
    motif = f"{prefixe}-{code_entite}-{annee}-"
    numeros = (
        db.query(Courrier.numero)
        .filter(Courrier.type == type_courrier, Courrier.numero.like(f"{motif}%"))
        .all()
    )
    max_seq = 0
    pattern = re.compile(rf"^{re.escape(motif)}(\d{{4}})$")
    for (numero,) in numeros:
        match = pattern.match(numero)
        if match:
            max_seq = max(max_seq, int(match.group(1)))
    return f"{motif}{max_seq + 1:04d}"


async def sauvegarder_fichiers(
    db: Session,
    courrier: Courrier,
    fichiers: list[UploadFile],
    user_id: int,
) -> list[PieceJointe]:
    os.makedirs(settings.upload_dir, exist_ok=True)
    resultats: list[PieceJointe] = []

    for fichier in fichiers:
        if not fichier.filename:
            continue
        _, ext = os.path.splitext(fichier.filename)
        ext = ext.lower()
        if ext not in EXTENSIONS_AUTORISEES:
            raise ValueError(
                f"Extension non autorisée ({ext}). "
                f"Formats acceptés : {', '.join(sorted(EXTENSIONS_AUTORISEES))}"
            )

        contenu = await fichier.read()
        nom_stockage = f"{courrier.numero}_{uuid.uuid4().hex}{ext}"
        chemin_absolu = os.path.join(settings.upload_dir, nom_stockage)
        with open(chemin_absolu, "wb") as f:
            f.write(contenu)

        pj = PieceJointe(
            courrier_id=courrier.id,
            nom_original=fichier.filename,
            chemin_stockage=chemin_absolu,
            taille_octets=len(contenu),
            type_mime=fichier.content_type,
            uploaded_by=user_id,
        )
        db.add(pj)
        resultats.append(pj)

    return resultats


def courrier_vers_liste(c: Courrier) -> dict:
    return {
        "id": c.id,
        "numero": c.numero,
        "type": c.type,
        "entite_nom": c.entite.nom,
        "entite_code": c.entite.code,
        "objet": c.objet,
        "expediteur": c.expediteur,
        "destinataire": c.destinataire,
        "service_destinataire": c.service_destinataire,
        "service_emetteur": c.service_emetteur,
        "urgence": c.urgence,
        "statut": c.statut,
        "date_reception": c.date_reception,
        "nb_pieces_jointes": len(c.pieces_jointes),
        "created_at": c.created_at,
    }


def courrier_vers_detail(c: Courrier, role: str) -> dict:
    return {
        "id": c.id,
        "numero": c.numero,
        "type": c.type,
        "entite_id": c.entite_id,
        "entite_nom": c.entite.nom,
        "entite_code": c.entite.code,
        "date_reception": c.date_reception,
        "expediteur": c.expediteur,
        "reference_document": c.reference_document,
        "objet": c.objet,
        "service_destinataire": c.service_destinataire,
        "destinataire": c.destinataire,
        "adresse_destinataire": c.adresse_destinataire,
        "service_emetteur": c.service_emetteur,
        "corps_courrier": c.corps_courrier,
        "urgence": c.urgence,
        "statut": c.statut,
        "observations": c.observations,
        "pieces_jointes": c.pieces_jointes,
        "statuts_possibles": statuts_possibles(role, c.statut),
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }


def lister_courriers(
    db: Session,
    type_courrier: str,
    filtre_statut: str | None = None,
    recherche: str | None = None,
    entite_id: int | None = None,
) -> list[dict]:
    query = (
        db.query(Courrier)
        .options(joinedload(Courrier.entite), joinedload(Courrier.pieces_jointes))
        .filter(Courrier.type == type_courrier)
    )
    if filtre_statut:
        query = query.filter(Courrier.statut == filtre_statut)
    if entite_id:
        query = query.filter(Courrier.entite_id == entite_id)
    if recherche:
        terme = f"%{recherche.strip()}%"
        query = query.filter(
            or_(
                Courrier.numero.ilike(terme),
                Courrier.objet.ilike(terme),
                Courrier.expediteur.ilike(terme),
                Courrier.destinataire.ilike(terme),
            )
        )
    courriers = query.order_by(Courrier.created_at.desc()).all()
    return [courrier_vers_liste(c) for c in courriers]


async def creer_courrier_entrant(
    db: Session,
    user: User,
    entite_id: int,
    expediteur: str,
    objet: str,
    service_destinataire: str,
    date_reception: str | None,
    reference_document: str | None,
    urgence: str,
    observations: str | None,
    fichiers: list[UploadFile],
) -> Courrier:
    if not expediteur.strip():
        raise ValueError("L'expéditeur est obligatoire.")
    if not objet.strip():
        raise ValueError("L'objet est obligatoire.")
    if not service_destinataire.strip():
        raise ValueError("Le service destinataire est obligatoire.")
    if urgence not in URGENCES_VALIDES:
        raise ValueError("Urgence invalide.")

    entite = db.query(Entite).filter(Entite.id == entite_id, Entite.actif.is_(True)).first()
    if entite is None:
        raise ValueError("Entité introuvable.")

    numero = generer_numero(db, "entrant", entite.code)
    courrier = Courrier(
        numero=numero,
        type="entrant",
        entite_id=entite_id,
        date_reception=date_reception,
        expediteur=expediteur.strip(),
        reference_document=reference_document,
        objet=objet.strip(),
        service_destinataire=service_destinataire.strip(),
        urgence=urgence,
        statut="en_attente",
        observations=observations,
        created_by=user.id,
    )
    db.add(courrier)
    db.flush()

    db.add(
        StatutLog(
            courrier_id=courrier.id,
            ancien_statut=None,
            nouveau_statut="en_attente",
            user_id=user.id,
            observation="Création",
        )
    )

    if fichiers:
        await sauvegarder_fichiers(db, courrier, fichiers, user.id)

    enregistrer_audit(
        db, user.id, "creation_courrier", f"Courrier {numero}", "courriers"
    )
    db.commit()
    db.refresh(courrier)
    return courrier


def changer_statut_courrier(
    db: Session,
    user: User,
    courrier_id: int,
    nouveau_statut: str,
    observation: str | None,
) -> Courrier:
    courrier = (
        db.query(Courrier)
        .options(joinedload(Courrier.entite), joinedload(Courrier.pieces_jointes))
        .filter(Courrier.id == courrier_id)
        .first()
    )
    if courrier is None:
        raise ValueError("Courrier introuvable.")

    ancien = courrier.statut
    if not transition_autorisee(user.role, ancien, nouveau_statut):
        raise ValueError(
            f"Transition non autorisée : {ancien} → {nouveau_statut} "
            f"pour le rôle « {user.role} »."
        )

    courrier.statut = nouveau_statut
    courrier.updated_at = datetime.now()
    db.add(
        StatutLog(
            courrier_id=courrier.id,
            ancien_statut=ancien,
            nouveau_statut=nouveau_statut,
            user_id=user.id,
            observation=observation,
        )
    )
    enregistrer_audit(
        db,
        user.id,
        "changement_statut",
        f"{courrier.numero} : {ancien} → {nouveau_statut}",
        "courriers",
    )
    db.commit()
    db.refresh(courrier)
    return courrier


def obtenir_historique(db: Session, courrier_id: int) -> list[dict]:
    logs = (
        db.query(StatutLog)
        .options(joinedload(StatutLog.utilisateur))
        .filter(StatutLog.courrier_id == courrier_id)
        .order_by(StatutLog.date.asc())
        .all()
    )
    resultat = []
    for log in logs:
        nom = None
        if log.utilisateur:
            nom = f"{log.utilisateur.prenom} {log.utilisateur.nom}"
        resultat.append(
            {
                "id": log.id,
                "ancien_statut": log.ancien_statut,
                "nouveau_statut": log.nouveau_statut,
                "observation": log.observation,
                "date": log.date,
                "utilisateur_nom": nom,
            }
        )
    return resultat


def stats_dashboard(db: Session) -> dict:
    total = db.query(func.count(Courrier.id)).scalar() or 0
    en_attente = (
        db.query(func.count(Courrier.id)).filter(Courrier.statut == "en_attente").scalar()
        or 0
    )
    transmis = (
        db.query(func.count(Courrier.id)).filter(Courrier.statut == "transmis").scalar()
        or 0
    )
    valides = (
        db.query(func.count(Courrier.id)).filter(Courrier.statut == "valide").scalar() or 0
    )

    par_entite_rows = (
        db.query(Entite.nom, func.count(Courrier.id))
        .outerjoin(Courrier, Courrier.entite_id == Entite.id)
        .group_by(Entite.id, Entite.nom)
        .all()
    )
    par_entite = {nom: count for nom, count in par_entite_rows}

    return {
        "total_courriers": total,
        "en_attente": en_attente,
        "transmis": transmis,
        "valides": valides,
        "par_entite": par_entite,
    }


def lister_entites(db: Session) -> list[Entite]:
    return db.query(Entite).filter(Entite.actif.is_(True)).order_by(Entite.nom).all()


def lister_services(db: Session) -> list[Service]:
    return db.query(Service).filter(Service.actif.is_(True)).order_by(Service.nom).all()
