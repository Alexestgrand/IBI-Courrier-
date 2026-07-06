import { useEffect, useState } from "react";
import { api } from "../api/client";
import AlerteErreur from "../components/AlerteErreur";
import { useToast } from "../context/ToastContext";
import { formatDate } from "../utils";

const ROLES = [
  "admin",
  "dg",
  "reception",
  "comptabilite",
  "marche",
  "achat",
];

const FORM_VIDE = {
  nom: "",
  prenom: "",
  email: "",
  role: "reception",
  mot_de_passe: "",
  actif: true,
};

const genererMotDePasse = (longueur = 12) => {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789";
  return Array.from({ length: longueur }, () =>
    chars.charAt(Math.floor(Math.random() * chars.length))
  ).join("");
};

export default function Utilisateurs() {
  const { toast } = useToast();
  const [users, setUsers] = useState([]);
  const [audit, setAudit] = useState([]);
  const [recherche, setRecherche] = useState("");
  const [roleFiltre, setRoleFiltre] = useState("");
  const [form, setForm] = useState(FORM_VIDE);
  const [editId, setEditId] = useState(null);
  const [erreur, setErreur] = useState("");
  const [message, setMessage] = useState("");
  const [loadingListe, setLoadingListe] = useState(true);
  const [erreurListe, setErreurListe] = useState("");

  const charger = () => {
    setLoadingListe(true);
    setErreurListe("");
    Promise.all([
      api.utilisateurs({ recherche: recherche || undefined, role: roleFiltre || undefined }),
      api.audit({ limite: 20 }),
    ])
      .then(([u, a]) => {
        setUsers(u);
        setAudit(a);
      })
      .catch((err) => {
        setErreurListe(err.message || "Impossible de charger les utilisateurs.");
      })
      .finally(() => setLoadingListe(false));
  };

  useEffect(() => {
    charger();
  }, [roleFiltre]);

  const resetForm = () => {
    setForm(FORM_VIDE);
    setEditId(null);
  };

  const soumettre = async (e) => {
    e.preventDefault();
    setErreur("");
    setMessage("");
    try {
      if (editId) {
        await api.modifierUtilisateur(editId, {
          nom: form.nom,
          prenom: form.prenom,
          email: form.email,
          role: form.role,
          actif: form.actif,
        });
        setMessage("Utilisateur modifié.");
        toast("Utilisateur modifié.", "success");
      } else {
        await api.creerUtilisateur(form);
        setMessage("Utilisateur créé.");
        toast("Utilisateur créé.", "success");
      }
      resetForm();
      charger();
    } catch (err) {
      setErreur(err.message);
    }
  };

  const editer = (u) => {
    setEditId(u.id);
    setForm({
      nom: u.nom,
      prenom: u.prenom,
      email: u.email,
      role: u.role,
      mot_de_passe: "",
      actif: u.actif,
    });
  };

  const resetMdp = async (id) => {
    if (!confirm("Réinitialiser le mot de passe de cet utilisateur ?")) return;
    const propose = genererMotDePasse();
    const saisie = prompt(
      "Saisissez le nouveau mot de passe (min. 6 caractères).\n" +
        "Vous pouvez modifier la proposition ci-dessous :",
      propose
    );
    if (!saisie) return;
    if (saisie.length < 6) {
      toast("Le mot de passe doit contenir au moins 6 caractères.", "error");
      return;
    }
    try {
      await api.resetMotDePasse(id, saisie);
      toast(
        "Mot de passe réinitialisé. Communiquez-le à l'utilisateur de manière sécurisée.",
        "success",
        8000
      );
    } catch (err) {
      toast(err.message, "error");
    }
  };

  const toggleActif = async (u) => {
    try {
      await api.modifierUtilisateur(u.id, { actif: !u.actif });
      charger();
      toast(u.actif ? "Utilisateur désactivé." : "Utilisateur activé.", "success");
    } catch (err) {
      toast(err.message, "error");
    }
  };

  return (
    <div>
      <h2 className="page-title" style={{ marginBottom: "1.25rem" }}>Gestion des utilisateurs</h2>

      <div className="toolbar">
        <input
          placeholder="Rechercher…"
          value={recherche}
          onChange={(e) => setRecherche(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && charger()}
        />
        <select value={roleFiltre} onChange={(e) => setRoleFiltre(e.target.value)}>
          <option value="">Tous rôles</option>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <button className="btn btn-secondary" onClick={charger}>
          Filtrer
        </button>
      </div>

      <form onSubmit={soumettre} className="panel form-grid">
        <h3 className="panel__title" style={{ gridColumn: "1 / -1", marginBottom: 0 }}>
          {editId ? "Modifier utilisateur" : "Nouvel utilisateur"}
        </h3>
        <div className="form-group">
          <label>Prénom</label>
          <input value={form.prenom} onChange={(e) => setForm({ ...form, prenom: e.target.value })} required />
        </div>
        <div className="form-group">
          <label>Nom</label>
          <input value={form.nom} onChange={(e) => setForm({ ...form, nom: e.target.value })} required />
        </div>
        <div className="form-group">
          <label>E-mail</label>
          <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        </div>
        <div className="form-group">
          <label>Rôle</label>
          <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </div>
        {!editId && (
          <div className="form-group">
            <label>Mot de passe</label>
            <input
              type="password"
              value={form.mot_de_passe}
              onChange={(e) => setForm({ ...form, mot_de_passe: e.target.value })}
              required
            />
          </div>
        )}
        {editId && (
          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={form.actif}
                onChange={(e) => setForm({ ...form, actif: e.target.checked })}
              />{" "}
              Actif
            </label>
          </div>
        )}
        {erreur && <p className="error-msg" style={{ gridColumn: "1 / -1" }}>{erreur}</p>}
        {message && <p className="success-msg" style={{ gridColumn: "1 / -1" }}>{message}</p>}
        <div className="actions-row" style={{ gridColumn: "1 / -1" }}>
          <button type="submit" className="btn btn-primary">
            {editId ? "Enregistrer" : "Créer"}
          </button>
          {editId && (
            <button type="button" className="btn btn-secondary" onClick={resetForm}>
              Annuler
            </button>
          )}
        </div>
      </form>

      <AlerteErreur message={erreurListe} onRetry={charger} />

      <div className="panel table-wrap">
        {loadingListe ? (
          <p className="loading-text">Chargement…</p>
        ) : erreurListe ? null : users.length === 0 ? (
          <p className="empty-state">Aucun utilisateur trouvé.</p>
        ) : (
        <table>
          <thead>
            <tr>
              <th>Nom</th>
              <th>E-mail</th>
              <th>Rôle</th>
              <th>Statut</th>
              <th>Dernière connexion</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>
                  {u.prenom} {u.nom}
                </td>
                <td>{u.email}</td>
                <td>{u.role}</td>
                <td>{u.actif ? "Actif" : "Inactif"}</td>
                <td>{u.derniere_connexion ? formatDate(u.derniere_connexion) : "—"}</td>
                <td>
                  <div className="actions-row">
                    <button className="btn btn-secondary btn-sm" onClick={() => editer(u)}>
                      Modifier
                    </button>
                    <button className="btn btn-secondary btn-sm" onClick={() => resetMdp(u.id)}>
                      MDP
                    </button>
                    <button className="btn btn-secondary btn-sm" onClick={() => toggleActif(u)}>
                      {u.actif ? "Désactiver" : "Activer"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        )}
      </div>

      <div className="panel">
        <h3 className="panel__title">Journal d&apos;audit (20 dernières entrées)</h3>
        {audit.map((a) => (
          <div key={a.id} className="historique-item">
            <strong>{a.action}</strong>
            <div className="text-secondary">{a.detail}</div>
            <div className="text-muted" style={{ fontSize: "0.8rem" }}>
              {a.utilisateur_nom || "—"} — {a.module} — {formatDate(a.date)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
