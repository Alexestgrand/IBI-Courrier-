import { useEffect, useState } from "react";
import { api } from "../api/client";
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

export default function Utilisateurs() {
  const [users, setUsers] = useState([]);
  const [audit, setAudit] = useState([]);
  const [recherche, setRecherche] = useState("");
  const [roleFiltre, setRoleFiltre] = useState("");
  const [form, setForm] = useState(FORM_VIDE);
  const [editId, setEditId] = useState(null);
  const [erreur, setErreur] = useState("");
  const [message, setMessage] = useState("");

  const charger = () => {
    api.utilisateurs({ recherche: recherche || undefined, role: roleFiltre || undefined }).then(setUsers);
    api.audit({ limite: 20 }).then(setAudit);
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
      } else {
        await api.creerUtilisateur(form);
        setMessage("Utilisateur créé.");
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
    try {
      const res = await api.resetMotDePasse(id);
      alert(`Nouveau mot de passe : ${res.mot_de_passe}`);
    } catch (err) {
      alert(err.message);
    }
  };

  const toggleActif = async (u) => {
    try {
      await api.modifierUtilisateur(u.id, { actif: !u.actif });
      charger();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div>
      <h2 className="page-title">Gestion des utilisateurs</h2>

      <div className="toolbar glass-inner">
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

      <form onSubmit={soumettre} className="card glass-inner form-grid" style={{ marginTop: "1rem" }}>
        <h3 style={{ gridColumn: "1 / -1" }}>
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
        {message && <p style={{ gridColumn: "1 / -1", color: "var(--succes)" }}>{message}</p>}
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

      <div className="card glass-inner" style={{ marginTop: "1rem", overflowX: "auto" }}>
        <table className="data-table">
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
                    <button className="btn btn-secondary" style={{ padding: "0.25rem 0.5rem", fontSize: "0.75rem" }} onClick={() => editer(u)}>
                      Modifier
                    </button>
                    <button className="btn btn-secondary" style={{ padding: "0.25rem 0.5rem", fontSize: "0.75rem" }} onClick={() => resetMdp(u.id)}>
                      MDP
                    </button>
                    <button className="btn btn-secondary" style={{ padding: "0.25rem 0.5rem", fontSize: "0.75rem" }} onClick={() => toggleActif(u)}>
                      {u.actif ? "Désactiver" : "Activer"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card glass-inner" style={{ marginTop: "1rem" }}>
        <h3>Journal d&apos;audit (20 dernières entrées)</h3>
        {audit.map((a) => (
          <div key={a.id} className="historique-item">
            <strong>{a.action}</strong>
            <div style={{ color: "var(--texte-secondaire)" }}>{a.detail}</div>
            <div style={{ fontSize: "0.8rem", color: "var(--texte-secondaire)" }}>
              {a.utilisateur_nom || "—"} — {a.module} — {formatDate(a.date)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
