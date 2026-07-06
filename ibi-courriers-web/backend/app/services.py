"""Services métier."""

import os
import re
import uuid
from datetime import date, datetime, timezone

from fastapi import UploadFile
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session, joinedload

from app.authorization import (
    appliquer_filtre_acces_courrier,
    peut_supprimer_courrier,
    service_impose_pour_role,
    verifier_acces_courrier,
    verifier_suppression_courrier,
)
from app.uploads import valider_contenu_upload
from app.config import settings
from app.constants import (
    TRANSITIONS_PAR_ROLE,
    TRANSITIONS_VALIDES,
    URGENCES_VALIDES,
    service_pour_role,
)
from app.database import engine
from app.models import AuditLog, Courrier, Entite, Notification, PieceJointe, Service, StatutLog, User

MAX_RECHERCHE_EXPORT = 5000


def _filtre_mois_egal(coalesce_ts, mois_yyyy_mm: str):
    """Filtre calendaire YYYY-MM compatible PostgreSQL (prod) et SQLite (tests)."""
    if engine.dialect.name == "postgresql":
        return func.to_char(coalesce_ts, "YYYY-MM") == mois_yyyy_mm
    return func.strftime("%Y-%m", coalesce_ts) == mois_yyyy_mm


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
        contenu = await fichier.read()
        ext = valider_contenu_upload(contenu, fichier.filename)

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


def courrier_vers_detail(c: Courrier, role: str, user: User | None = None) -> dict:
    signe_par_nom = None
    if getattr(c, "signataire", None):
        signe_par_nom = f"{c.signataire.prenom} {c.signataire.nom}"

    import_scan = c.corps_courrier == "(Courrier importé - PDF scanné)"
    peut_signer = bool(
        user
        and c.type == "sortant"
        and c.statut in ("valide", "archive")
        and user.role in ("dg", "admin")
        and user.chemin_signature
        and c.signe_par_id is None
        and not import_scan
    )

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
        "chemin_pdf": c.chemin_pdf,
        "signe_par_nom": signe_par_nom,
        "signe_le": c.signe_le,
        "peut_signer": peut_signer,
        "peut_supprimer": bool(user and peut_supprimer_courrier(user, c)),
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
    service: str | None = None,
    mon_service: bool = False,
    role_utilisateur: str | None = None,
    page: int = 1,
    page_size: int = 25,
    urgents_seulement: bool = False,
) -> dict:
    page = max(1, page)
    page_size = min(max(1, page_size), 100)

    query = (
        db.query(Courrier)
        .options(joinedload(Courrier.entite), joinedload(Courrier.pieces_jointes))
        .filter(Courrier.type == type_courrier)
    )
    if filtre_statut:
        query = query.filter(Courrier.statut == filtre_statut)
    if urgents_seulement:
        query = query.filter(
            Courrier.urgence.in_(("urgent", "très urgent")),
            Courrier.statut.notin_(("valide", "rejete", "archive")),
        )
    if entite_id:
        query = query.filter(Courrier.entite_id == entite_id)

    filtre_service = service
    if role_utilisateur:
        service_force = service_impose_pour_role(role_utilisateur)
        if service_force:
            filtre_service = service_force
        elif mon_service and not filtre_service:
            filtre_service = service_pour_role(role_utilisateur)
    if filtre_service:
        if type_courrier == "entrant":
            query = query.filter(Courrier.service_destinataire == filtre_service)
        else:
            query = query.filter(Courrier.service_emetteur == filtre_service)

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

    total = query.count()
    pages = max(1, (total + page_size - 1) // page_size)
    if page > pages:
        page = pages

    courriers = (
        query.order_by(Courrier.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [courrier_vers_liste(c) for c in courriers],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


def lister_a_valider(
    db: Session,
    page: int = 1,
    page_size: int = 25,
) -> dict:
    """Courriers entrants transmis, triés par urgence puis ancienneté."""
    page = max(1, page)
    page_size = min(max(1, page_size), 100)

    urgence_order = case(
        (Courrier.urgence == "très urgent", 0),
        (Courrier.urgence == "urgent", 1),
        else_=2,
    )

    query = (
        db.query(Courrier)
        .options(joinedload(Courrier.entite), joinedload(Courrier.pieces_jointes))
        .filter(Courrier.type == "entrant", Courrier.statut == "transmis")
    )

    total = query.count()
    pages = max(1, (total + page_size - 1) // page_size)
    if page > pages:
        page = pages

    courriers = (
        query.order_by(urgence_order, Courrier.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [courrier_vers_liste(c) for c in courriers],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


def stats_rapport_mensuel(db: Session, annee: int, mois: int) -> dict:
    """Statistiques pour le rapport mensuel PDF."""
    if mois < 1 or mois > 12:
        raise ValueError("Mois invalide.")

    debut = datetime(annee, mois, 1, tzinfo=timezone.utc)
    if mois == 12:
        fin = datetime(annee + 1, 1, 1, tzinfo=timezone.utc)
    else:
        fin = datetime(annee, mois + 1, 1, tzinfo=timezone.utc)

    courriers = (
        db.query(Courrier)
        .filter(Courrier.created_at >= debut, Courrier.created_at < fin)
        .all()
    )

    courrier_ids = [c.id for c in courriers]
    logs_par_courrier: dict[int, StatutLog] = {}
    if courrier_ids:
        logs_traitement = (
            db.query(StatutLog)
            .filter(
                StatutLog.courrier_id.in_(courrier_ids),
                StatutLog.nouveau_statut.in_(("valide", "rejete")),
            )
            .order_by(StatutLog.courrier_id, StatutLog.date.asc())
            .all()
        )
        for log in logs_traitement:
            if log.courrier_id not in logs_par_courrier:
                logs_par_courrier[log.courrier_id] = log

    par_service: dict[str, int] = {}
    par_statut: dict[str, int] = {}
    delais_par_service: dict[str, list[float]] = {}

    for courrier in courriers:
        service = (
            courrier.service_destinataire
            or courrier.service_emetteur
            or "Non renseigné"
        )
        par_service[service] = par_service.get(service, 0) + 1
        par_statut[courrier.statut] = par_statut.get(courrier.statut, 0) + 1

        log = logs_par_courrier.get(courrier.id)
        if log and courrier.created_at:
            created = courrier.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            traite = log.date
            if traite.tzinfo is None:
                traite = traite.replace(tzinfo=timezone.utc)
            jours = (traite - created).total_seconds() / 86400
            delais_par_service.setdefault(service, []).append(jours)

    delais_moyens = {
        service: round(sum(valeurs) / len(valeurs), 1)
        for service, valeurs in delais_par_service.items()
        if valeurs
    }

    return {
        "annee": annee,
        "mois": mois,
        "total": len(courriers),
        "par_service": dict(
            sorted(par_service.items(), key=lambda item: item[1], reverse=True)
        ),
        "par_statut": par_statut,
        "delais_moyens_jours": dict(
            sorted(delais_moyens.items(), key=lambda item: item[1], reverse=True)
        ),
    }


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

    from app.services_notifications import notifier_nouveau_courrier

    try:
        notifier_nouveau_courrier(db, courrier)
    except Exception:
        pass

    db.commit()
    db.refresh(courrier)

    from app.email_service import notifier_courrier_entrant

    try:
        notifier_courrier_entrant(db, courrier)
    except Exception:
        pass

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

    verifier_acces_courrier(user, courrier)

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

    from app.services_notifications import notifier_changement_statut

    try:
        notifier_changement_statut(db, courrier, ancien, nouveau_statut, user.id)
    except Exception:
        pass

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


def stats_dashboard(db: Session, user: User | None = None) -> dict:
    aujourd_hui = date.today()

    def q_courriers():
        query = db.query(Courrier)
        if user:
            query = appliquer_filtre_acces_courrier(query, user)
        return query

    total = q_courriers().count()
    en_attente = q_courriers().filter(Courrier.statut == "en_attente").count()
    transmis = q_courriers().filter(Courrier.statut == "transmis").count()
    valides = q_courriers().filter(Courrier.statut == "valide").count()
    urgents = (
        q_courriers()
        .filter(
            Courrier.urgence.in_(("urgent", "très urgent")),
            Courrier.statut.in_(("en_attente", "transmis")),
        )
        .count()
    )

    par_entite_rows = (
        q_courriers()
        .join(Entite, Courrier.entite_id == Entite.id)
        .with_entities(Entite.nom, func.count(Courrier.id))
        .group_by(Entite.id, Entite.nom)
        .all()
    )
    par_entite = {nom: count for nom, count in par_entite_rows}

    mois_actuel = datetime.now(timezone.utc).strftime("%Y-%m")
    par_service: dict[str, int] = {}
    service_user = service_impose_pour_role(user.role) if user else None
    services_cibles = (
        db.query(Service).filter(Service.actif.is_(True), Service.nom == service_user).all()
        if service_user
        else db.query(Service).filter(Service.actif.is_(True)).all()
    )
    for service in services_cibles:
        count = (
            q_courriers()
            .filter(
                or_(
                    Courrier.service_destinataire == service.nom,
                    Courrier.service_emetteur == service.nom,
                ),
                _filtre_mois_egal(
                    func.coalesce(Courrier.updated_at, Courrier.created_at),
                    mois_actuel,
                ),
            )
            .count()
        )
        if count > 0:
            par_service[service.nom] = count
    par_service = dict(sorted(par_service.items(), key=lambda x: x[1], reverse=True))

    urgents_rows = (
        q_courriers()
        .options(joinedload(Courrier.entite), joinedload(Courrier.pieces_jointes))
        .filter(
            Courrier.urgence.in_(("urgent", "très urgent")),
            Courrier.statut.notin_(("valide", "rejete", "archive")),
        )
        .order_by(Courrier.created_at.desc())
        .limit(15)
        .all()
    )

    recents_rows = (
        q_courriers()
        .options(joinedload(Courrier.entite), joinedload(Courrier.pieces_jointes))
        .order_by(Courrier.created_at.desc())
        .limit(10)
        .all()
    )

    recus_aujourdhui = (
        q_courriers()
        .options(joinedload(Courrier.entite), joinedload(Courrier.pieces_jointes))
        .filter(func.date(Courrier.created_at) == aujourd_hui)
        .order_by(Courrier.created_at.desc())
        .limit(20)
        .all()
    )

    ids_traites = (
        db.query(StatutLog.courrier_id)
        .filter(
            StatutLog.nouveau_statut.in_(("valide", "rejete", "archive")),
            func.date(StatutLog.date) == aujourd_hui,
        )
        .distinct()
        .all()
    )
    ids_traites_list = [row[0] for row in ids_traites]
    traites_aujourdhui = []
    if ids_traites_list:
        traites_aujourdhui = (
            q_courriers()
            .options(joinedload(Courrier.entite), joinedload(Courrier.pieces_jointes))
            .filter(Courrier.id.in_(ids_traites_list))
            .order_by(Courrier.updated_at.desc())
            .limit(20)
            .all()
        )

    return {
        "total_courriers": total,
        "en_attente": en_attente,
        "transmis": transmis,
        "valides": valides,
        "urgents": urgents,
        "par_entite": par_entite,
        "par_service": par_service,
        "recents": [courrier_vers_liste(c) for c in recents_rows],
        "courriers_urgents": [courrier_vers_liste(c) for c in urgents_rows],
        "journal_du_jour": {
            "date": aujourd_hui.isoformat(),
            "recus": [courrier_vers_liste(c) for c in recus_aujourdhui],
            "traites": [courrier_vers_liste(c) for c in traites_aujourdhui],
        },
    }


def lister_entites(db: Session) -> list[Entite]:
    return db.query(Entite).filter(Entite.actif.is_(True)).order_by(Entite.nom).all()


def lister_services(db: Session) -> list[Service]:
    return db.query(Service).filter(Service.actif.is_(True)).order_by(Service.nom).all()


def _parser_date_jjmmaaaa(texte: str) -> datetime | None:
    texte = texte.strip()
    if not texte:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(texte, fmt)
        except ValueError:
            continue
    raise ValueError("Date invalide : format attendu JJ/MM/AAAA ou AAAA-MM-JJ.")


def _date_courrier_pour_filtre(courrier: Courrier) -> datetime | None:
    if courrier.date_reception:
        try:
            return _parser_date_jjmmaaaa(courrier.date_reception)
        except ValueError:
            pass
    if courrier.created_at:
        return courrier.created_at.replace(tzinfo=None)
    return None


async def creer_courrier_sortant(
    db: Session,
    user: User,
    entite_id: int,
    destinataire: str,
    objet: str,
    service_emetteur: str,
    adresse_destinataire: str | None,
    urgence: str,
    observations: str | None,
    corps_courrier: str | None,
    pdf_scanne: UploadFile | None,
) -> Courrier:
    if not destinataire.strip():
        raise ValueError("Le destinataire est obligatoire.")
    if not objet.strip():
        raise ValueError("L'objet est obligatoire.")
    if not service_emetteur.strip():
        raise ValueError("Le service émetteur est obligatoire.")
    if urgence not in URGENCES_VALIDES:
        raise ValueError("Urgence invalide.")

    entite = db.query(Entite).filter(Entite.id == entite_id, Entite.actif.is_(True)).first()
    if entite is None:
        raise ValueError("Entité introuvable.")

    mode_import = pdf_scanne is not None and pdf_scanne.filename
    if mode_import:
        contenu = await pdf_scanne.read()
        valider_contenu_upload(contenu, pdf_scanne.filename or "import.pdf")
        corps_final = "(Courrier importé - PDF scanné)"
    else:
        if not corps_courrier or not corps_courrier.strip():
            raise ValueError("Le corps du courrier est obligatoire en mode saisie.")
        corps_final = corps_courrier.strip()

    numero = generer_numero(db, "sortant", entite.code)
    courrier = Courrier(
        numero=numero,
        type="sortant",
        entite_id=entite_id,
        date_reception=datetime.now().strftime("%d/%m/%Y"),
        destinataire=destinataire.strip(),
        adresse_destinataire=adresse_destinataire,
        objet=objet.strip(),
        service_emetteur=service_emetteur.strip(),
        corps_courrier=corps_final,
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

    exports_dir = os.path.join(settings.upload_dir, "exports")
    os.makedirs(exports_dir, exist_ok=True)
    chemin_pdf = os.path.join(exports_dir, f"{numero}.pdf")

    if mode_import:
        with open(chemin_pdf, "wb") as f:
            f.write(contenu)
    else:
        from app.pdf_export import generer_pdf_sortant

        db.refresh(courrier)
        courrier_charge = (
            db.query(Courrier)
            .options(joinedload(Courrier.entite), joinedload(Courrier.pieces_jointes))
            .filter(Courrier.id == courrier.id)
            .first()
        )
        generer_pdf_sortant(courrier_vers_detail(courrier_charge, user.role), chemin_pdf)

    courrier.chemin_pdf = chemin_pdf
    enregistrer_audit(
        db, user.id, "creation_courrier_sortant", f"Courrier {numero}", "courriers"
    )
    db.commit()
    db.refresh(courrier)
    return courrier


def modifier_courrier(
    db: Session,
    user: User,
    courrier_id: int,
    champs: dict,
) -> Courrier:
    courrier = (
        db.query(Courrier)
        .options(joinedload(Courrier.entite), joinedload(Courrier.pieces_jointes))
        .filter(Courrier.id == courrier_id)
        .first()
    )
    if courrier is None:
        raise ValueError("Courrier introuvable.")

    verifier_acces_courrier(user, courrier)

    if courrier.statut not in ("en_attente", "transmis"):
        raise ValueError("Seuls les courriers en attente ou transmis peuvent être modifiés.")

    champs_autorises = {
        "entrant": (
            "expediteur",
            "objet",
            "service_destinataire",
            "date_reception",
            "reference_document",
            "urgence",
            "observations",
        ),
        "sortant": (
            "destinataire",
            "adresse_destinataire",
            "objet",
            "service_emetteur",
            "corps_courrier",
            "urgence",
            "observations",
        ),
    }
    for cle, valeur in champs.items():
        if valeur is None or cle not in champs_autorises.get(courrier.type, ()):
            continue
        if cle == "urgence" and valeur not in URGENCES_VALIDES:
            raise ValueError("Urgence invalide.")
        setattr(courrier, cle, valeur.strip() if isinstance(valeur, str) else valeur)

    courrier.updated_at = datetime.now()
    enregistrer_audit(
        db,
        user.id,
        "modification_courrier",
        f"Courrier {courrier.numero}",
        "courriers",
    )
    db.commit()
    db.refresh(courrier)
    return courrier


def _supprimer_fichier_si_existe(chemin: str | None) -> None:
    if chemin and os.path.isfile(chemin):
        try:
            os.remove(chemin)
        except OSError:
            pass


def supprimer_courrier(db: Session, user: User, courrier_id: int) -> None:
    courrier = (
        db.query(Courrier)
        .options(joinedload(Courrier.pieces_jointes))
        .filter(Courrier.id == courrier_id)
        .first()
    )
    if courrier is None:
        raise ValueError("Courrier introuvable.")

    verifier_suppression_courrier(user, courrier)

    numero = courrier.numero
    for pj in courrier.pieces_jointes:
        _supprimer_fichier_si_existe(pj.chemin_stockage)
    _supprimer_fichier_si_existe(courrier.chemin_pdf)

    db.query(Notification).filter(Notification.courrier_id == courrier.id).delete(
        synchronize_session=False
    )
    enregistrer_audit(
        db,
        user.id,
        "suppression_courrier",
        f"Courrier {numero}",
        "courriers",
    )
    db.delete(courrier)
    db.commit()


def _requete_recherche_courriers(
    db: Session,
    user: User | None = None,
    mot_cle: str | None = None,
    type_courrier: str | None = None,
    statut: str | None = None,
    service: str | None = None,
    urgence: str | None = None,
    entite_id: int | None = None,
    date_debut: str | None = None,
    date_fin: str | None = None,
):
    query = (
        db.query(Courrier)
        .options(joinedload(Courrier.entite), joinedload(Courrier.pieces_jointes))
    )
    if user:
        query = appliquer_filtre_acces_courrier(query, user)

    if type_courrier:
        query = query.filter(Courrier.type == type_courrier)
    if statut:
        query = query.filter(Courrier.statut == statut)
    if urgence:
        query = query.filter(Courrier.urgence == urgence)
    if entite_id:
        query = query.filter(Courrier.entite_id == entite_id)
    if service:
        terme_service = f"%{service.strip()}%"
        query = query.filter(
            or_(
                Courrier.service_destinataire.ilike(terme_service),
                Courrier.service_emetteur.ilike(terme_service),
            )
        )
    if mot_cle:
        terme = f"%{mot_cle.strip()}%"
        query = query.filter(
            or_(
                Courrier.numero.ilike(terme),
                Courrier.objet.ilike(terme),
                Courrier.expediteur.ilike(terme),
                Courrier.destinataire.ilike(terme),
                Courrier.reference_document.ilike(terme),
                Courrier.observations.ilike(terme),
            )
        )

    debut = _parser_date_jjmmaaaa(date_debut) if date_debut else None
    fin = _parser_date_jjmmaaaa(date_fin) if date_fin else None
    if debut:
        query = query.filter(Courrier.created_at >= debut)
    if fin:
        fin_fin_journee = fin.replace(hour=23, minute=59, second=59)
        query = query.filter(Courrier.created_at <= fin_fin_journee)

    return query


def rechercher_courriers(
    db: Session,
    user: User | None = None,
    mot_cle: str | None = None,
    type_courrier: str | None = None,
    statut: str | None = None,
    service: str | None = None,
    urgence: str | None = None,
    entite_id: int | None = None,
    date_debut: str | None = None,
    date_fin: str | None = None,
    page: int = 1,
    page_size: int = 25,
) -> dict:
    page = max(1, page)
    page_size = min(max(1, page_size), 100)

    query = _requete_recherche_courriers(
        db,
        user,
        mot_cle=mot_cle,
        type_courrier=type_courrier,
        statut=statut,
        service=service,
        urgence=urgence,
        entite_id=entite_id,
        date_debut=date_debut,
        date_fin=date_fin,
    )

    total = query.count()
    pages = max(1, (total + page_size - 1) // page_size)
    if page > pages:
        page = pages

    courriers = (
        query.order_by(Courrier.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [courrier_vers_liste(c) for c in courriers],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


def rechercher_courriers_export(
    db: Session,
    user: User | None = None,
    mot_cle: str | None = None,
    type_courrier: str | None = None,
    statut: str | None = None,
    service: str | None = None,
    urgence: str | None = None,
    entite_id: int | None = None,
    date_debut: str | None = None,
    date_fin: str | None = None,
) -> list[dict]:
    query = _requete_recherche_courriers(
        db,
        user,
        mot_cle=mot_cle,
        type_courrier=type_courrier,
        statut=statut,
        service=service,
        urgence=urgence,
        entite_id=entite_id,
        date_debut=date_debut,
        date_fin=date_fin,
    )
    total = query.count()
    if total > MAX_RECHERCHE_EXPORT:
        raise ValueError(
            f"Trop de résultats ({total}). Affinez les filtres "
            f"(maximum {MAX_RECHERCHE_EXPORT} pour l'export)."
        )
    courriers = query.order_by(Courrier.created_at.desc()).all()
    return [courrier_vers_liste(c) for c in courriers]


def lister_audit(db: Session, module: str | None = None, limite: int = 50) -> list[dict]:
    query = (
        db.query(AuditLog)
        .options(joinedload(AuditLog.utilisateur))
        .order_by(AuditLog.date.desc())
    )
    if module:
        query = query.filter(AuditLog.module == module)
    logs = query.limit(limite).all()
    resultat = []
    for log in logs:
        nom = None
        if log.utilisateur:
            nom = f"{log.utilisateur.prenom} {log.utilisateur.nom}"
        resultat.append(
            {
                "id": log.id,
                "action": log.action,
                "detail": log.detail,
                "module": log.module,
                "date": log.date,
                "utilisateur_nom": nom,
            }
        )
    return resultat


def enregistrer_signature_utilisateur(
    db: Session, user: User, contenu_png: bytes
) -> str:
    sig_dir = os.path.join(settings.upload_dir, "signatures")
    os.makedirs(sig_dir, exist_ok=True)
    chemin = os.path.join(sig_dir, f"user_{user.id}.png")
    with open(chemin, "wb") as f:
        f.write(contenu_png)
    user.chemin_signature = chemin
    db.commit()
    return chemin


def supprimer_signature_utilisateur(db: Session, user: User) -> None:
    if user.chemin_signature and os.path.isfile(user.chemin_signature):
        os.remove(user.chemin_signature)
    user.chemin_signature = None
    db.commit()


def signer_courrier_sortant(db: Session, user: User, courrier_id: int) -> Courrier:
    if user.role not in ("dg", "admin"):
        raise ValueError("Seuls la DG et l'admin peuvent signer.")
    if not user.chemin_signature or not os.path.isfile(user.chemin_signature):
        raise ValueError("Enregistrez d'abord votre signature dans votre profil.")

    courrier = (
        db.query(Courrier)
        .options(
            joinedload(Courrier.entite),
            joinedload(Courrier.pieces_jointes),
            joinedload(Courrier.signataire),
        )
        .filter(Courrier.id == courrier_id)
        .first()
    )
    if courrier is None:
        raise ValueError("Courrier introuvable.")
    verifier_acces_courrier(user, courrier)
    if courrier.type != "sortant":
        raise ValueError("La signature s'applique aux courriers sortants.")
    if courrier.statut not in ("valide", "archive"):
        raise ValueError("Le courrier doit être validé avant signature.")
    if courrier.corps_courrier == "(Courrier importé - PDF scanné)":
        raise ValueError("Signature indisponible sur un PDF importé.")
    if courrier.signe_par_id is not None:
        raise ValueError("Ce courrier est déjà signé.")

    from app.pdf_export import generer_pdf_sortant

    exports_dir = os.path.join(settings.upload_dir, "exports")
    os.makedirs(exports_dir, exist_ok=True)
    chemin_pdf = os.path.join(exports_dir, f"{courrier.numero}.pdf")

    detail = courrier_vers_detail(courrier, user.role, user)
    detail["signature_chemin"] = user.chemin_signature
    detail["signataire_nom"] = f"{user.prenom} {user.nom}"
    generer_pdf_sortant(detail, chemin_pdf)

    courrier.chemin_pdf = chemin_pdf
    courrier.signe_par_id = user.id
    courrier.signe_le = datetime.now(timezone.utc)

    enregistrer_audit(
        db,
        user.id,
        "signature_courrier",
        f"Signature {courrier.numero}",
        "courriers",
    )
    db.commit()
    db.refresh(courrier)
    return courrier
