# IBI COURRIERS

Application de gestion électronique des courriers **entrants** et **sortants** pour le **Groupe IBI Côte d'Ivoire**.

---

## Présentation

- Gestion du cycle de vie des courriers : enregistrement, suivi des statuts, pièces jointes, export PDF.
- Application **desktop Windows**, **100 % hors ligne** : aucune connexion réseau au runtime.
- Données stockées localement dans une base **SQLite** (`courriers.db`) et des dossiers fichiers (`uploads/`, `exports/`, `backups/`).
- Interface graphique **CustomTkinter** (thème sombre), fenêtre **1280×720** pixels.
- Traçabilité des actions via un **journal d'audit**.

---

## Prérequis

| Contexte | Exigence |
|----------|----------|
| **Système** | Windows 10 ou 11 |
| **Développement** | Python **3.11+** |
| **Production** | Exécutable **PyInstaller** (`.exe`) ou installation Python équivalente |
| **Écran** | Résolution minimale recommandée 1280×720 |

---

## Installation (développement)

```bash
pip install customtkinter pillow reportlab bcrypt tkcalendar
python main.py
```

Au premier lancement, l'application crée automatiquement :

- la base `courriers.db` ;
- les dossiers `uploads/`, `exports/`, `backups/` ;
- un compte administrateur par défaut (voir [Compte par défaut](#compte-par-défaut-développement)).

---

## Premier lancement

1. Lancer `python main.py` (ou l'exécutable PyInstaller).
2. Se connecter avec le compte admin (développement) ou les identifiants fournis par l'administrateur.
3. Le **tableau de bord** s'affiche après connexion ; la barre latérale permet d'accéder aux modules selon le rôle.

---

## Guide utilisateur

### Connexion

- Saisir **e-mail** et **mot de passe**.
- Touche **Entrée** ou bouton **Se connecter**.
- En cas d'échec, un message d'erreur s'affiche (identifiants incorrects, compte désactivé, etc.).
- **Déconnexion** : bouton en bas de la barre latérale.

### Tableau de bord

- **Cartes** : total courriers, à traiter, urgents, validés ce mois.
- **Répartition par statut** : 5 barres (En attente, Transmis, Validé, Rejeté, Archivé).
- **Activité récente** : cliquer une ligne pour ouvrir la fiche du courrier.
- **Courriers très urgents non traités** : liste cliquable + badge si présence d'urgents.
- **Courriers par service** : statistiques du mois en cours.
- Rafraîchissement automatique des données toutes les **5 minutes** ; horloge mise à jour chaque minute.

> **À traiter** regroupe les statuts *En attente* et *Transmis*.  
> **Validés ce mois** compte les courriers au statut *Validé* ou *Archivé* modifiés ce mois-ci.

### Affichage plein écran

- **F11** : basculer plein écran / fenêtré (également depuis l'écran de connexion).
- **Échap** : quitter le plein écran sans fermer l'application.
- Bouton **⛶** en haut de la barre latérale (après connexion).

### Courriers entrants

- Liste filtrable par statut et recherche textuelle.
- **Nouveau courrier** : formulaire modal avec **calendrier** pour la date (expéditeur, objet, service, urgence, pièce jointe…).
- Numérotation automatique : `ENT-AAAA-NNNN`.
- Bouton **Voir** : fiche détail, changement de statut selon le rôle, export PDF, pièce jointe.

**Recherche dans la liste** : N°, objet, expéditeur, référence document (insensible à la casse).

### Courriers sortants

- Même principe que les entrants, avec **calendrier** pour la date d'envoi.
- Numérotation : `SOR-AAAA-NNNN`.
- Deux modes de création :
  - **Saisir le contenu** : génération d'une lettre **PDF** (ReportLab) à l'enregistrement.
  - **Importer un PDF scanné** : le fichier PDF sélectionné est copié comme document officiel (pas de lettre générée).
- Réimpression / ouverture du PDF depuis la fiche ou la liste.

**Recherche dans la liste** : N°, objet, destinataire, référence document.

### Recherche avancée

Filtres combinables : mot-clé, type (entrant/sortant), statut, service, urgence, plage de dates (calendrier **Date du** / **Date au**, bouton ✕ pour effacer).

Le **mot-clé** recherche dans :

- numéro (`ENT-…`, `SOR-…`) ;
- objet, observations ;
- expéditeur, destinataire ;
- référence document.

Exemples : `ENT-2026`, `0001`, `SOR-2026-0003`.

Export **PDF** du rapport de résultats.

### Sauvegardes (admin et DG)

- **Créer une sauvegarde maintenant** : copie complète de `courriers.db` + `uploads/` + `exports/`.
- **Restaurer** : remplace les données actuelles ; une sauvegarde de sécurité est créée dans `backups/_pre_restore/` avant restauration.
- **Redémarrer l'application** après restauration si la base était verrouillée.
- **Purge** : suppression automatique des copies de plus de 30 jours (minimum 5 conservées).

#### Sauvegarde automatique — à comprendre

| Tâche | Fréquence | Action |
|-------|-----------|--------|
| **Sauvegarde quotidienne** | Chaque jour à **00:00** | Crée une nouvelle copie complète |
| **Tâche hebdomadaire** | Tous les **7 jours** | **Purge** des anciennes sauvegardes (> 30 jours) — **ce n'est pas** une sauvegarde supplémentaire |

Les deux tâches peuvent être activées ou désactivées depuis l'écran Sauvegardes (session en cours).

### Utilisateurs (admin uniquement)

- Création, modification, activation/désactivation des comptes.
- Réinitialisation de mot de passe (mot de passe temporaire affiché une seule fois).
- Journal d'activité filtrable (Connexion, Courriers, Recherche, Utilisateurs, Système).

Garde-fous : impossible de se désactiver soi-même, ni de supprimer le dernier administrateur actif.

---

## Rôles et permissions

| Rôle | Accès principal |
|------|-----------------|
| **admin** | Tout + Utilisateurs + Sauvegardes |
| **dg** | Validation / rejet, archivage, Sauvegardes |
| **reception** | Enregistrement entrants, passage *En attente* → *Transmis* |
| **comptabilite**, **marche**, **achat** | Consultation selon modules assignés |

Les transitions de statut autorisées dépendent du rôle (voir [Statuts](#statuts-et-workflow)).

---

## Statuts et workflow

### Statuts en base (5 valeurs)

| Code DB | Libellé interface |
|---------|-------------------|
| `en_attente` | En attente |
| `transmis` | Transmis |
| `valide` | Validé |
| `rejete` | Rejeté |
| `archive` | Archivé |

### Équivalence cahier des charges

> Dans le cahier des charges, le statut **« Traité »** correspond au statut **« Validé »** (`valide`) en base.  
> L'ancienne valeur `traite` a été migrée vers `valide` au démarrage. Il n'existe **pas** de 6ᵉ statut séparé « traité ».

### Transitions typiques

```
En attente → Transmis → Validé → Archivé
                      ↘ Rejeté → Archivé
```

- **Réception** : En attente → Transmis  
- **DG / Admin** : Transmis → Validé ou Rejeté ; Validé/Rejeté → Archivé  

---

## Documentation technique

### Architecture MVC

| Couche | Dossier | Rôle |
|--------|---------|------|
| **Vue** | `views/` | Interface CustomTkinter uniquement |
| **Service** | `services/` | Logique métier, orchestration |
| **Modèle** | `database/models.py` | Schéma SQL, migrations, requêtes |
| **Utilitaires** | `utils/` | PDF, backup, audit, thème UI |

Règles :

- Aucune requête SQL dans les vues.
- Mots de passe hashés avec **bcrypt**.
- Actions utilisateur enregistrées dans `audit_log`.
- Chemins relatifs via `RACINE_PROJET` (`database/db.py`).

### Structure des dossiers

```
ibi-courriers/
├── main.py              # Point d'entrée
├── courriers.db         # Base SQLite (créée au 1er lancement)
├── assets/              # Logo et ressources statiques
├── uploads/             # Pièces jointes courriers entrants
├── exports/             # PDF courriers sortants générés
├── backups/             # Sauvegardes horodatées
│   └── _pre_restore/    # Copies de sécurité avant restauration
├── database/
│   ├── db.py            # Connexion, init_db
│   └── models.py          # Tables, migrations, SQL
├── services/            # auth, courriers, recherche, stats, utilisateurs
├── utils/               # backup, scheduler, audit, export_pdf, theme…
└── views/               # login, dashboard, listes, fiches, sauvegardes…
```

### Base de données

Tables principales :

- **users** — comptes, rôles, `derniere_connexion`
- **courriers** — entrants et sortants (champ `type`)
- **services** — services métier actifs
- **statuts_log** — historique des changements de statut
- **audit_log** — journal des actions applicatives

Migrations légères idempotentes au démarrage (`migrer_schema()`).

### Dépendances Python

| Package | Usage |
|---------|--------|
| `customtkinter` | Interface graphique |
| `pillow` | Affichage logo / images |
| `reportlab` | Génération PDF |
| `bcrypt` | Hash des mots de passe |
| `tkcalendar` | Sélecteur de date (formulaires et recherche) |

Modules standard : `sqlite3`, `threading` (scheduler backup), `shutil`, `secrets`.

### PyInstaller (production)

Build **onedir** (pas `--onefile`) : SQLite et fichiers persistants doivent rester **à côté de l'exécutable**, pas dans `_internal\`.

Chemins :
- **Données utilisateur** (`courriers.db`, `uploads\`, `exports\`, `backups\`) : répertoire de `IBI_COURRIERS.exe` (`utils/chemin_app.py` → `determiner_racine_projet()`).
- **Assets en lecture** (logo UI/PDF) : `_internal\` via `_MEIPASS` (`chemin_asset()` / `get_resource_path()`).

Commande :

```bash
pip install pyinstaller
pyinstaller build.spec --noconfirm
```

Ou sous Windows : `build.bat` (installe les dépendances, build, copie les README dans `dist\IBI_COURRIERS\`).

Documentation livrée avec le build :
- `README_INSTALLATION.txt` — déploiement et compte initial `admin@ibi.local` / `admin123`
- `README_TECHNIQUE.txt` — stack, emplacements des données, sauvegardes

**Important** : ne pas embarquer `courriers.db`, `uploads/`, `exports/` ni `backups/` dans le spec PyInstaller. `init_db()` et les helpers `creer_dossier_*()` les créent au premier lancement.

---

## Compte par défaut (développement)

Créé uniquement si la table `users` est vide :

| Champ | Valeur |
|-------|--------|
| E-mail | `admin@ibi.local` |
| Mot de passe | `admin123` |
| Rôle | admin |

**Changer ce mot de passe en production.**

---

## Audit

Chaque action sensible est enregistrée dans `audit_log` (module, action, détail, utilisateur, date).

Modules d'audit : `auth`, `courriers`, `recherche`, `users`, `systeme`.

Consultation : écran **Utilisateurs** → section **Journal d'activité** (admin).

---

## Dépannage rapide

| Problème | Piste |
|----------|--------|
| Erreur au démarrage DB | Vérifier les droits d'écriture sur le dossier projet |
| Restauration échouée | Fermer l'application et relancer ; la DB SQLite est verrouillée tant que l'app tourne |
| PDF sortant introuvable | Vérifier `exports/` et le champ `chemin_pdf` en base |
| Connexion impossible | Compte désactivé ou mot de passe réinitialisé par l'admin |

---

## Version

**IBI COURRIERS v1.1** (1.1.0) — Groupe IBI Côte d'Ivoire.

### Nouveautés v1.1

- Calendrier de saisie des dates (courriers entrants/sortants, recherche)
- Courrier sortant : saisie du contenu ou import d'un PDF scanné
- Mode plein écran (F11, bouton sidebar, Échap pour quitter)
- Correctifs modales et calendrier en plein écran (Windows)
