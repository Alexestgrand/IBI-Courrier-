"""Schéma SQLite, initialisation des tables et données de test."""

import re
import sqlite3
from datetime import datetime
from typing import Any

import bcrypt

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    mot_de_passe TEXT NOT NULL,
    role TEXT NOT NULL CHECK (
        role IN ('admin', 'dg', 'reception', 'comptabilite', 'marche', 'achat')
    ),
    actif INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    actif INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS courriers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL CHECK (type IN ('entrant', 'sortant')),
    date_reception TEXT,
    expediteur TEXT,
    reference_document TEXT,
    objet TEXT NOT NULL,
    service_destinataire TEXT,
    urgence TEXT NOT NULL DEFAULT 'normal' CHECK (
        urgence IN ('normal', 'urgent', 'très urgent')
    ),
    statut TEXT NOT NULL DEFAULT 'en_attente',
    observations TEXT,
    fichier_joint TEXT,
    created_by INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT,
    FOREIGN KEY (created_by) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS statuts_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    courrier_id INTEGER NOT NULL,
    ancien_statut TEXT,
    nouveau_statut TEXT NOT NULL,
    user_id INTEGER,
    observation TEXT,
    date TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (courrier_id) REFERENCES courriers (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    detail TEXT,
    module TEXT,
    date TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (user_id) REFERENCES users (id)
);
"""


def _ligne_vers_dict(ligne: sqlite3.Row | None) -> dict[str, Any] | None:
    if ligne is None:
        return None
    return dict(ligne)


def _lignes_vers_liste(lignes: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(ligne) for ligne in lignes]


def creer_tables(connexion: sqlite3.Connection) -> None:
    """Crée toutes les tables si elles n'existent pas."""
    try:
        connexion.executescript(SCHEMA_SQL)
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la création des tables.") from erreur


def migrer_schema(connexion: sqlite3.Connection) -> None:
    """Applique les migrations légères idempotentes."""
    try:
        colonnes = {
            row[1]
            for row in connexion.execute("PRAGMA table_info(courriers)").fetchall()
        }
        colonnes_a_ajouter = {
            "reference_document": "TEXT",
            "destinataire": "TEXT",
            "adresse_destinataire": "TEXT",
            "corps_courrier": "TEXT",
            "service_emetteur": "TEXT",
            "chemin_pdf": "TEXT",
        }
        for nom_colonne, type_colonne in colonnes_a_ajouter.items():
            if nom_colonne not in colonnes:
                connexion.execute(
                    f"ALTER TABLE courriers ADD COLUMN {nom_colonne} {type_colonne}"
                )

        connexion.execute(
            "UPDATE courriers SET statut = 'en_attente' WHERE statut = 'enregistre'"
        )
        connexion.execute(
            "UPDATE courriers SET statut = 'valide' WHERE statut = 'traite'"
        )

        colonnes_users = {
            row[1]
            for row in connexion.execute("PRAGMA table_info(users)").fetchall()
        }
        if "derniere_connexion" not in colonnes_users:
            connexion.execute(
                "ALTER TABLE users ADD COLUMN derniere_connexion TEXT"
            )
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la migration du schéma.") from erreur


def inserer_donnees_test(connexion: sqlite3.Connection) -> None:
    """Insère l'utilisateur admin et les services par défaut si absents."""
    try:
        curseur = connexion.cursor()

        if curseur.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            mot_de_passe_hash = bcrypt.hashpw(
                b"admin123", bcrypt.gensalt()
            ).decode("utf-8")
            curseur.execute(
                """
                INSERT INTO users (nom, prenom, email, mot_de_passe, role, actif)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("Admin", "IBI", "admin@ibi.local", mot_de_passe_hash, "admin", 1),
            )

        for nom_service in ("Direction", "Comptabilité", "Service Marché"):
            curseur.execute(
                "INSERT OR IGNORE INTO services (nom, actif) VALUES (?, 1)",
                (nom_service,),
            )
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de l'insertion des données de test.") from erreur


def obtenir_utilisateur_par_email(
    connexion: sqlite3.Connection, email: str
) -> sqlite3.Row | None:
    """Retourne un utilisateur actif par email, ou None."""
    try:
        return connexion.execute(
            """
            SELECT * FROM users
            WHERE LOWER(email) = LOWER(?) AND actif = 1
            """,
            (email.strip(),),
        ).fetchone()
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la recherche de l'utilisateur.") from erreur


def obtenir_utilisateur_par_id(
    connexion: sqlite3.Connection, user_id: int
) -> sqlite3.Row | None:
    """Retourne un utilisateur actif par identifiant, ou None."""
    try:
        return connexion.execute(
            """
            SELECT * FROM users
            WHERE id = ? AND actif = 1
            """,
            (user_id,),
        ).fetchone()
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la recherche de l'utilisateur.") from erreur


def inserer_audit_log(
    connexion: sqlite3.Connection,
    user_id: int | None,
    action: str,
    detail: str | None,
    module: str | None,
) -> None:
    """Insère une entrée dans le journal d'audit."""
    try:
        connexion.execute(
            """
            INSERT INTO audit_log (user_id, action, detail, module)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, action, detail, module),
        )
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de l'enregistrement de l'audit.") from erreur


def compter_courriers(connexion: sqlite3.Connection) -> int:
    """Retourne le nombre total de courriers (entrants + sortants)."""
    try:
        return int(connexion.execute("SELECT COUNT(*) FROM courriers").fetchone()[0])
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec du comptage des courriers.") from erreur


def obtenir_tous_utilisateurs(
    connexion: sqlite3.Connection,
    recherche: str | None = None,
    role: str | None = None,
) -> list[dict[str, Any]]:
    """Liste tous les utilisateurs (actifs et inactifs) pour l'administration."""
    try:
        requete = """
            SELECT id, nom, prenom, email, role, actif, created_at, derniere_connexion
            FROM users
            WHERE 1=1
        """
        parametres: list[Any] = []

        if recherche:
            terme = f"%{recherche.strip()}%"
            requete += """
                AND (
                    LOWER(nom) LIKE LOWER(?)
                    OR LOWER(prenom) LIKE LOWER(?)
                    OR LOWER(email) LIKE LOWER(?)
                )
            """
            parametres.extend([terme, terme, terme])

        if role:
            requete += " AND role = ?"
            parametres.append(role)

        requete += " ORDER BY nom, prenom"

        lignes = connexion.execute(requete, parametres).fetchall()
        return _lignes_vers_liste(lignes)
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la récupération des utilisateurs.") from erreur


def obtenir_utilisateur_admin_par_id(
    connexion: sqlite3.Connection, user_id: int
) -> dict[str, Any] | None:
    """Retourne un utilisateur par id sans filtre actif."""
    try:
        ligne = connexion.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return _ligne_vers_dict(ligne)
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la récupération de l'utilisateur.") from erreur


def email_utilisateur_existe(
    connexion: sqlite3.Connection, email: str, exclure_id: int | None = None
) -> bool:
    """Vérifie si un email est déjà utilisé par un autre utilisateur."""
    try:
        requete = "SELECT id FROM users WHERE LOWER(email) = LOWER(?)"
        parametres: list[Any] = [email.strip()]
        if exclure_id is not None:
            requete += " AND id != ?"
            parametres.append(exclure_id)
        return connexion.execute(requete, parametres).fetchone() is not None
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la vérification de l'email.") from erreur


def creer_utilisateur(connexion: sqlite3.Connection, data: dict[str, Any]) -> int:
    """Insère un nouvel utilisateur et retourne son identifiant."""
    try:
        curseur = connexion.execute(
            """
            INSERT INTO users (prenom, nom, email, role, mot_de_passe, actif)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data["prenom"],
                data["nom"],
                data["email"],
                data["role"],
                data["mot_de_passe_hash"],
                data["actif"],
            ),
        )
        return int(curseur.lastrowid)
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la création de l'utilisateur.") from erreur


def mettre_a_jour_utilisateur(
    connexion: sqlite3.Connection, user_id: int, data: dict[str, Any]
) -> None:
    """Met à jour les informations d'un utilisateur (sans mot de passe)."""
    try:
        connexion.execute(
            """
            UPDATE users
            SET prenom = ?, nom = ?, email = ?, role = ?, actif = ?
            WHERE id = ?
            """,
            (
                data["prenom"],
                data["nom"],
                data["email"],
                data["role"],
                data["actif"],
                user_id,
            ),
        )
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la mise à jour de l'utilisateur.") from erreur


def basculer_actif_utilisateur(
    connexion: sqlite3.Connection, user_id: int, actif: int
) -> None:
    """Active ou désactive un utilisateur."""
    try:
        connexion.execute(
            "UPDATE users SET actif = ? WHERE id = ?",
            (actif, user_id),
        )
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec du changement de statut utilisateur.") from erreur


def reinitialiser_mot_de_passe_utilisateur(
    connexion: sqlite3.Connection, user_id: int, mot_de_passe_hash: str
) -> None:
    """Réinitialise le mot de passe hashé d'un utilisateur."""
    try:
        connexion.execute(
            "UPDATE users SET mot_de_passe = ? WHERE id = ?",
            (mot_de_passe_hash, user_id),
        )
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la réinitialisation du mot de passe.") from erreur


def mettre_a_jour_derniere_connexion(
    connexion: sqlite3.Connection, user_id: int
) -> None:
    """Enregistre la date/heure de dernière connexion."""
    try:
        connexion.execute(
            """
            UPDATE users
            SET derniere_connexion = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (user_id,),
        )
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la mise à jour de la dernière connexion.") from erreur


def compter_admins_actifs(connexion: sqlite3.Connection) -> int:
    """Compte les administrateurs actifs."""
    try:
        return int(
            connexion.execute(
                """
                SELECT COUNT(*) FROM users
                WHERE role = 'admin' AND actif = 1
                """
            ).fetchone()[0]
        )
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec du comptage des administrateurs.") from erreur


def obtenir_journal_audit(
    connexion: sqlite3.Connection,
    limit: int = 20,
    module: str | None = None,
) -> list[dict[str, Any]]:
    """Retourne les dernières entrées du journal d'audit."""
    try:
        requete = """
            SELECT a.*, u.prenom, u.nom, u.email
            FROM audit_log a
            LEFT JOIN users u ON a.user_id = u.id
            WHERE 1=1
        """
        parametres: list[Any] = []

        if module:
            requete += " AND a.module = ?"
            parametres.append(module)

        requete += " ORDER BY a.date DESC, a.id DESC LIMIT ?"
        parametres.append(limit)

        lignes = connexion.execute(requete, parametres).fetchall()
        return _lignes_vers_liste(lignes)
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la récupération du journal d'audit.") from erreur


STATUTS_REPARTITION: tuple[str, ...] = (
    "en_attente",
    "transmis",
    "valide",
    "rejete",
    "archive",
)


def obtenir_stats_dashboard(connexion: sqlite3.Connection) -> dict[str, Any]:
    """Statistiques completes du tableau de bord (entrants + sortants)."""
    try:
        total = connexion.execute("SELECT COUNT(*) FROM courriers").fetchone()[0]

        en_attente = connexion.execute(
            """
            SELECT COUNT(*) FROM courriers
            WHERE statut IN ('en_attente', 'transmis')
            """
        ).fetchone()[0]

        urgents = connexion.execute(
            """
            SELECT COUNT(*) FROM courriers
            WHERE urgence IN ('urgent', 'très urgent')
              AND statut NOT IN ('valide', 'rejete', 'archive')
            """
        ).fetchone()[0]

        traites_mois = connexion.execute(
            """
            SELECT COUNT(*) FROM courriers
            WHERE statut IN ('valide', 'archive')
              AND strftime(
                    '%Y-%m',
                    COALESCE(updated_at, created_at)
                  ) = strftime('%Y-%m', 'now', 'localtime')
            """
        ).fetchone()[0]

        repartition: dict[str, int] = {s: 0 for s in STATUTS_REPARTITION}
        for ligne in connexion.execute(
            """
            SELECT statut, COUNT(*) AS nb
            FROM courriers
            GROUP BY statut
            """
        ).fetchall():
            if ligne["statut"] in repartition:
                repartition[ligne["statut"]] = int(ligne["nb"])

        return {
            "cartes": {
                "total": int(total),
                "en_attente": int(en_attente),
                "urgents": int(urgents),
                "traites_mois": int(traites_mois),
            },
            "repartition_statut": repartition,
        }
    except sqlite3.Error as erreur:
        raise RuntimeError("Echec du calcul des statistiques dashboard.") from erreur


def obtenir_stats_tableau_bord(connexion: sqlite3.Connection) -> dict[str, int]:
    """Compatibilite : retourne uniquement les cartes du dashboard."""
    return obtenir_stats_dashboard(connexion)["cartes"]


def obtenir_activite_recente(
    connexion: sqlite3.Connection, limit: int = 10
) -> list[dict[str, Any]]:
    """Derniers courriers modifies ou crees."""
    try:
        lignes = connexion.execute(
            """
            SELECT * FROM courriers
            ORDER BY COALESCE(updated_at, created_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return _lignes_vers_liste(lignes)
    except sqlite3.Error as erreur:
        raise RuntimeError("Echec de la recuperation de l'activite recente.") from erreur


def obtenir_stats_par_service(connexion: sqlite3.Connection) -> dict[str, int]:
    """Nombre de courriers du mois courant par service actif."""
    try:
        services = obtenir_services_actifs(connexion)
        resultat: dict[str, int] = {}
        for service in services:
            nom = service["nom"]
            count = connexion.execute(
                """
                SELECT COUNT(*) FROM courriers
                WHERE (service_destinataire = ? OR service_emetteur = ?)
                  AND strftime(
                        '%Y-%m',
                        COALESCE(updated_at, created_at)
                      ) = strftime('%Y-%m', 'now', 'localtime')
                """,
                (nom, nom),
            ).fetchone()[0]
            resultat[nom] = int(count)
        return dict(sorted(resultat.items(), key=lambda x: x[1], reverse=True))
    except sqlite3.Error as erreur:
        raise RuntimeError("Echec du calcul des stats par service.") from erreur


def obtenir_courriers_urgents_non_traites(
    connexion: sqlite3.Connection,
) -> list[dict[str, Any]]:
    """Courriers tres urgents non clotures."""
    try:
        lignes = connexion.execute(
            """
            SELECT * FROM courriers
            WHERE urgence = 'très urgent'
              AND statut NOT IN ('valide', 'rejete', 'archive')
            ORDER BY COALESCE(updated_at, created_at) DESC
            """
        ).fetchall()
        return _lignes_vers_liste(lignes)
    except sqlite3.Error as erreur:
        raise RuntimeError(
            "Echec de la recuperation des courriers urgents."
        ) from erreur


def obtenir_services_actifs(connexion: sqlite3.Connection) -> list[dict[str, Any]]:
    """Liste des services actifs (id, nom)."""
    try:
        lignes = connexion.execute(
            """
            SELECT id, nom FROM services
            WHERE actif = 1
            ORDER BY nom
            """
        ).fetchall()
        return _lignes_vers_liste(lignes)
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la récupération des services.") from erreur


def obtenir_numero_auto(connexion: sqlite3.Connection, type_courrier: str) -> str:
    """Génère le prochain numéro automatique ENT-YYYY-NNNN ou SOR-YYYY-NNNN."""
    try:
        annee = datetime.now().year
        prefixe = "ENT" if type_courrier == "entrant" else "SOR"
        motif = f"{prefixe}-{annee}-"
        lignes = connexion.execute(
            """
            SELECT numero FROM courriers
            WHERE type = ? AND numero LIKE ?
            """,
            (type_courrier, f"{motif}%"),
        ).fetchall()

        max_seq = 0
        pattern = re.compile(rf"^{re.escape(motif)}(\d{{4}})$")
        for ligne in lignes:
            match = pattern.match(ligne["numero"])
            if match:
                max_seq = max(max_seq, int(match.group(1)))

        return f"{motif}{max_seq + 1:04d}"
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la génération du numéro.") from erreur


def obtenir_courriers_entrants(
    connexion: sqlite3.Connection,
    filtre_statut: str | None = None,
    recherche: str | None = None,
) -> list[dict[str, Any]]:
    """Liste des courriers entrants avec filtres optionnels."""
    try:
        requete = """
            SELECT * FROM courriers
            WHERE type = 'entrant'
        """
        params: list[Any] = []

        if filtre_statut:
            requete += " AND statut = ?"
            params.append(filtre_statut)

        if recherche and recherche.strip():
            terme = f"%{recherche.strip()}%"
            requete += """
                AND (
                    LOWER(objet) LIKE LOWER(?)
                    OR LOWER(expediteur) LIKE LOWER(?)
                    OR LOWER(numero) LIKE LOWER(?)
                    OR LOWER(COALESCE(reference_document, '')) LIKE LOWER(?)
                )
            """
            params.extend([terme, terme, terme, terme])

        requete += " ORDER BY created_at DESC"
        lignes = connexion.execute(requete, params).fetchall()
        return _lignes_vers_liste(lignes)
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la récupération des courriers.") from erreur


def obtenir_courrier_par_id(
    connexion: sqlite3.Connection, courrier_id: int
) -> dict[str, Any] | None:
    """Retourne un courrier par identifiant."""
    try:
        ligne = connexion.execute(
            "SELECT * FROM courriers WHERE id = ?",
            (courrier_id,),
        ).fetchone()
        return _ligne_vers_dict(ligne)
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la récupération du courrier.") from erreur


def creer_courrier(connexion: sqlite3.Connection, data: dict[str, Any]) -> int:
    """Insère un courrier (entrant ou sortant) et retourne son identifiant."""
    try:
        curseur = connexion.execute(
            """
            INSERT INTO courriers (
                numero, type, date_reception, expediteur, reference_document,
                objet, service_destinataire, urgence, statut, observations,
                fichier_joint, destinataire, adresse_destinataire, corps_courrier,
                service_emetteur, chemin_pdf, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                      datetime('now', 'localtime'),
                      datetime('now', 'localtime'))
            """,
            (
                data["numero"],
                data["type"],
                data.get("date_reception"),
                data.get("expediteur"),
                data.get("reference_document"),
                data["objet"],
                data.get("service_destinataire"),
                data.get("urgence", "normal"),
                data.get("statut", "en_attente"),
                data.get("observations"),
                data.get("fichier_joint"),
                data.get("destinataire"),
                data.get("adresse_destinataire"),
                data.get("corps_courrier"),
                data.get("service_emetteur"),
                data.get("chemin_pdf"),
                data.get("created_by"),
            ),
        )
        return int(curseur.lastrowid)
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la création du courrier.") from erreur


def inserer_log_statut(
    connexion: sqlite3.Connection,
    courrier_id: int,
    ancien_statut: str | None,
    nouveau_statut: str,
    user_id: int | None,
    observation: str | None,
) -> None:
    """Insère une entrée dans statuts_log."""
    try:
        connexion.execute(
            """
            INSERT INTO statuts_log (
                courrier_id, ancien_statut, nouveau_statut, user_id, observation
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (courrier_id, ancien_statut, nouveau_statut, user_id, observation),
        )
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de l'enregistrement de l'historique.") from erreur


def mettre_a_jour_statut(
    connexion: sqlite3.Connection,
    courrier_id: int,
    nouveau_statut: str,
    user_id: int,
    observation: str | None,
) -> None:
    """Met à jour le statut d'un courrier et journalise le changement."""
    try:
        ligne = connexion.execute(
            "SELECT statut FROM courriers WHERE id = ?",
            (courrier_id,),
        ).fetchone()
        if ligne is None:
            raise RuntimeError("Courrier introuvable.")

        ancien_statut = ligne["statut"]
        connexion.execute(
            """
            UPDATE courriers
            SET statut = ?, updated_at = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (nouveau_statut, courrier_id),
        )
        inserer_log_statut(
            connexion,
            courrier_id,
            ancien_statut,
            nouveau_statut,
            user_id,
            observation,
        )
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la mise à jour du statut.") from erreur


def obtenir_historique_statuts(
    connexion: sqlite3.Connection, courrier_id: int
) -> list[dict[str, Any]]:
    """Historique des statuts d'un courrier avec nom utilisateur."""
    try:
        lignes = connexion.execute(
            """
            SELECT s.*, u.nom, u.prenom
            FROM statuts_log s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE s.courrier_id = ?
            ORDER BY s.date DESC
            """,
            (courrier_id,),
        ).fetchall()
        return _lignes_vers_liste(lignes)
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la récupération de l'historique.") from erreur


def obtenir_courriers_sortants(
    connexion: sqlite3.Connection,
    filtre_statut: str | None = None,
    recherche: str | None = None,
) -> list[dict[str, Any]]:
    """Liste des courriers sortants avec filtres optionnels."""
    try:
        requete = """
            SELECT * FROM courriers
            WHERE type = 'sortant'
        """
        params: list[Any] = []

        if filtre_statut:
            requete += " AND statut = ?"
            params.append(filtre_statut)

        if recherche and recherche.strip():
            terme = f"%{recherche.strip()}%"
            requete += """
                AND (
                    LOWER(objet) LIKE LOWER(?)
                    OR LOWER(destinataire) LIKE LOWER(?)
                    OR LOWER(numero) LIKE LOWER(?)
                    OR LOWER(COALESCE(reference_document, '')) LIKE LOWER(?)
                )
            """
            params.extend([terme, terme, terme, terme])

        requete += " ORDER BY created_at DESC"
        lignes = connexion.execute(requete, params).fetchall()
        return _lignes_vers_liste(lignes)
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la récupération des courriers sortants.") from erreur


def creer_courrier_sortant(connexion: sqlite3.Connection, data: dict[str, Any]) -> int:
    """Insère un courrier sortant."""
    payload = {
        **data,
        "type": "sortant",
        "expediteur": None,
        "reference_document": None,
        "service_destinataire": None,
        "statut": data.get("statut", "en_attente"),
    }
    return creer_courrier(connexion, payload)


def mettre_a_jour_chemin_pdf(
    connexion: sqlite3.Connection, courrier_id: int, chemin_pdf: str
) -> None:
    """Met à jour le chemin PDF d'un courrier sortant."""
    try:
        connexion.execute(
            """
            UPDATE courriers
            SET chemin_pdf = ?, updated_at = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (chemin_pdf, courrier_id),
        )
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la mise à jour du chemin PDF.") from erreur


def _date_courrier_entier(courrier: dict[str, Any]) -> int:
    """Convertit la date d'un courrier en entier YYYYMMDD pour comparaison."""
    date_reception = courrier.get("date_reception")
    if date_reception and "/" in str(date_reception):
        try:
            jour, mois, annee = str(date_reception).split("/")
            return int(annee) * 10000 + int(mois) * 100 + int(jour)
        except (ValueError, IndexError):
            pass

    created_at = str(courrier.get("created_at") or "")
    if len(created_at) >= 10 and created_at[4] == "-":
        try:
            annee = int(created_at[0:4])
            mois = int(created_at[5:7])
            jour = int(created_at[8:10])
            return annee * 10000 + mois * 100 + jour
        except ValueError:
            pass
    return 0


def recherche_courriers(
    connexion: sqlite3.Connection,
    *,
    mot_cle: str | None = None,
    type_courrier: str | None = None,
    statut: str | None = None,
    service: str | None = None,
    urgence: str | None = None,
    date_debut: int | None = None,
    date_fin: int | None = None,
) -> list[dict[str, Any]]:
    """Recherche avancée de courriers avec filtres combinés (AND)."""
    try:
        requete = "SELECT * FROM courriers WHERE 1=1"
        params: list[Any] = []

        if type_courrier:
            requete += " AND type = ?"
            params.append(type_courrier)

        if statut:
            requete += " AND statut = ?"
            params.append(statut)

        if urgence:
            requete += " AND urgence = ?"
            params.append(urgence)

        if service:
            requete += " AND (service_destinataire = ? OR service_emetteur = ?)"
            params.extend([service, service])

        if mot_cle and mot_cle.strip():
            terme = f"%{mot_cle.strip()}%"
            requete += """
                AND (
                    LOWER(objet) LIKE LOWER(?)
                    OR LOWER(COALESCE(observations, '')) LIKE LOWER(?)
                    OR LOWER(COALESCE(expediteur, '')) LIKE LOWER(?)
                    OR LOWER(COALESCE(destinataire, '')) LIKE LOWER(?)
                    OR LOWER(COALESCE(reference_document, '')) LIKE LOWER(?)
                    OR LOWER(numero) LIKE LOWER(?)
                )
            """
            params.extend([terme, terme, terme, terme, terme, terme])

        requete += " ORDER BY created_at DESC"
        lignes = connexion.execute(requete, params).fetchall()
        resultats = _lignes_vers_liste(lignes)

        if date_debut is not None or date_fin is not None:
            filtres: list[dict[str, Any]] = []
            for courrier in resultats:
                date_entier = _date_courrier_entier(courrier)
                if date_entier == 0:
                    continue
                if date_debut is not None and date_entier < date_debut:
                    continue
                if date_fin is not None and date_entier > date_fin:
                    continue
                filtres.append(courrier)
            resultats = filtres

        return resultats
    except sqlite3.Error as erreur:
        raise RuntimeError("Échec de la recherche de courriers.") from erreur


get_courriers_entrants = obtenir_courriers_entrants
get_courrier_par_id = obtenir_courrier_par_id
get_courriers_sortants = obtenir_courriers_sortants
create_courrier_sortant = creer_courrier_sortant
search_courriers = recherche_courriers
get_stats_dashboard = obtenir_stats_dashboard
get_activite_recente = obtenir_activite_recente
get_stats_par_service = obtenir_stats_par_service
get_courriers_urgents_non_traites = obtenir_courriers_urgents_non_traites
get_all_users = obtenir_tous_utilisateurs
create_user = creer_utilisateur
update_user = mettre_a_jour_utilisateur
get_audit_log = obtenir_journal_audit
get_user_by_id_admin = obtenir_utilisateur_admin_par_id
count_courriers = compter_courriers
