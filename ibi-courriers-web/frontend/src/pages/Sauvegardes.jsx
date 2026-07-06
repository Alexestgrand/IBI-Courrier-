import { useEffect, useState } from "react";
import { api, downloadBackup } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { formatDate, formatTaille } from "../utils";

export default function Sauvegardes() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [backups, setBackups] = useState([]);
  const [smtp, setSmtp] = useState(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [testEmail, setTestEmail] = useState(user?.email || "");
  const [restoreFile, setRestoreFile] = useState("");
  const [restoreConfirm, setRestoreConfirm] = useState("");
  const [migration, setMigration] = useState(null);
  const [migrationFile, setMigrationFile] = useState(null);
  const [migrationRunning, setMigrationRunning] = useState(false);

  const charger = () => {
    setLoading(true);
    Promise.all([api.listBackups(), api.smtpStatus(), api.migrationStatus()])
      .then(([b, s, m]) => {
        setBackups(b);
        setSmtp(s);
        setMigration(m);
      })
      .catch((e) => toast(e.message, "error"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    charger();
  }, []);

  const creer = async () => {
    setCreating(true);
    try {
      const res = await api.createBackup();
      toast(res.message || "Sauvegarde créée.", "success");
      charger();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setCreating(false);
    }
  };

  const testerEmail = async () => {
    try {
      const res = await api.testSmtp(testEmail);
      toast(res.message, "success");
    } catch (e) {
      toast(e.message, "error");
    }
  };

  const restaurer = async () => {
    if (!restoreFile) {
      toast("Sélectionnez un fichier de sauvegarde base.", "error");
      return;
    }
    try {
      const res = await api.restoreBackup(restoreFile, restoreConfirm);
      toast(res.message, "success");
      setRestoreConfirm("");
    } catch (e) {
      toast(e.message, "error");
    }
  };

  const envoyerMigration = async () => {
    if (!migrationFile) {
      toast("Sélectionnez le fichier courriers.db.", "error");
      return;
    }
    try {
      const res = await api.uploadMigrationDb(migrationFile);
      toast(res.message, "success");
      setMigrationFile(null);
      charger();
    } catch (e) {
      toast(e.message, "error");
    }
  };

  const lancerMigration = async (dryRun) => {
    setMigrationRunning(true);
    try {
      const res = await api.runMigration("IBI", dryRun);
      const stats = res.stats
        ? ` — ${res.stats.courriers} courriers, ${res.stats.utilisateurs} utilisateurs`
        : "";
      toast(`${res.message}${stats}`, "success");
      if (!dryRun) charger();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setMigrationRunning(false);
    }
  };

  const fichiersDb = backups.filter((b) => b.type === "database");

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Administration</h2>
        <button
          className="btn btn-primary"
          onClick={creer}
          disabled={creating}
        >
          {creating ? "Sauvegarde…" : "Nouvelle sauvegarde"}
        </button>
      </div>

      <div className="panel">
        <h3 className="panel__title">Migration desktop (SQLite)</h3>
        <p className="panel__hint">
          Importez la base <code>courriers.db</code> de l&apos;application bureau
          vers PostgreSQL. Les doublons (même e-mail ou n° courrier) sont ignorés.
        </p>
        {migration?.pret ? (
          <p className="text-secondary" style={{ marginBottom: "1rem" }}>
            Fichier prêt : <strong>{migration.fichier}</strong> (
            {formatTaille(migration.taille_octets)})
          </p>
        ) : (
          <p className="text-muted" style={{ marginBottom: "1rem" }}>
            Aucun fichier courriers.db sur le serveur.
          </p>
        )}
        <div className="form-grid" style={{ maxWidth: 520 }}>
          <div className="form-group">
            <label>Fichier courriers.db</label>
            <input
              type="file"
              accept=".db"
              onChange={(e) => setMigrationFile(e.target.files?.[0] || null)}
            />
          </div>
          <div className="actions-row">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={envoyerMigration}
              disabled={!migrationFile}
            >
              Envoyer sur le serveur
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => lancerMigration(true)}
              disabled={!migration?.pret || migrationRunning}
            >
              Simuler
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => lancerMigration(false)}
              disabled={!migration?.pret || migrationRunning}
            >
              {migrationRunning ? "Migration…" : "Lancer la migration"}
            </button>
          </div>
        </div>
      </div>

      <div className="panel">
        <h3 className="panel__title">Notifications e-mail (SMTP)</h3>
        {smtp && (
          <p className="text-secondary" style={{ marginBottom: "1rem" }}>
            Statut :{" "}
            <strong>{smtp.enabled ? "Activé" : "Désactivé"}</strong>
            {smtp.enabled && smtp.host && ` — ${smtp.host}`}
          </p>
        )}
        <div className="form-grid" style={{ maxWidth: 480 }}>
          <div className="form-group">
            <label>E-mail de test</label>
            <input
              type="email"
              value={testEmail}
              onChange={(e) => setTestEmail(e.target.value)}
            />
          </div>
          <div className="actions-row" style={{ alignItems: "flex-end" }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={testerEmail}
              disabled={!smtp?.enabled}
            >
              Envoyer un test
            </button>
          </div>
        </div>
        {!smtp?.enabled && (
          <p className="text-muted" style={{ marginTop: "0.75rem" }}>
            SMTP en pause — activez SMTP_ENABLED dans le .env du serveur si besoin.
          </p>
        )}
      </div>

      <div className="panel">
        <h3 className="panel__title">Sauvegardes disponibles</h3>
        {loading ? (
          <p className="loading-text">Chargement…</p>
        ) : backups.length === 0 ? (
          <p className="empty-state">Aucune sauvegarde. Créez-en une ci-dessus.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Fichier</th>
                  <th>Type</th>
                  <th>Taille</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {backups.map((b) => (
                  <tr key={b.nom}>
                    <td>{b.nom}</td>
                    <td>{b.type === "database" ? "Base" : "Fichiers"}</td>
                    <td>{formatTaille(b.taille_octets)}</td>
                    <td>{formatDate(b.date)}</td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() =>
                          downloadBackup(b.nom).catch((e) =>
                            toast(e.message, "error")
                          )
                        }
                      >
                        Télécharger
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="panel">
        <h3 className="panel__title">Restaurer la base de données</h3>
        <p className="alert-banner">
          Attention : la restauration remplace les données actuelles. À utiliser
          uniquement en cas d&apos;urgence.
        </p>
        <div className="form-grid" style={{ maxWidth: 520 }}>
          <div className="form-group">
            <label>Fichier de sauvegarde (base)</label>
            <select
              value={restoreFile}
              onChange={(e) => setRestoreFile(e.target.value)}
            >
              <option value="">— Choisir —</option>
              {fichiersDb.map((b) => (
                <option key={b.nom} value={b.nom}>
                  {b.nom}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Confirmation (saisir RESTAURER)</label>
            <input
              value={restoreConfirm}
              onChange={(e) => setRestoreConfirm(e.target.value)}
              placeholder="RESTAURER"
            />
          </div>
          <div>
            <button type="button" className="btn btn-danger" onClick={restaurer}>
              Restaurer
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
