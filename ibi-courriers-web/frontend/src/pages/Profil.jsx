import { useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Profil() {
  const { user } = useAuth();
  const [ancien, setAncien] = useState("");
  const [nouveau, setNouveau] = useState("");
  const [confirm, setConfirm] = useState("");
  const [erreur, setErreur] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErreur("");
    setMessage("");
    if (nouveau !== confirm) {
      setErreur("Les mots de passe ne correspondent pas.");
      return;
    }
    if (nouveau.length < 6) {
      setErreur("Le mot de passe doit contenir au moins 6 caractères.");
      return;
    }
    setLoading(true);
    try {
      await api.changePassword(ancien, nouveau);
      setMessage("Mot de passe modifié avec succès.");
      setAncien("");
      setNouveau("");
      setConfirm("");
    } catch (err) {
      setErreur(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="page-title" style={{ marginBottom: "1.25rem" }}>Mon profil</h2>

      <div className="panel" style={{ marginBottom: "1rem" }}>
        <dl className="detail-grid">
          <dt>Nom</dt>
          <dd>
            {user?.prenom} {user?.nom}
          </dd>
          <dt>E-mail</dt>
          <dd>{user?.email}</dd>
          <dt>Rôle</dt>
          <dd>{user?.role}</dd>
        </dl>
      </div>

      <form onSubmit={handleSubmit} className="panel form-grid">
        <h3 className="panel__title" style={{ gridColumn: "1 / -1", marginBottom: 0 }}>Changer le mot de passe</h3>
        <div className="form-group">
          <label>Ancien mot de passe</label>
          <input type="password" value={ancien} onChange={(e) => setAncien(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Nouveau mot de passe</label>
          <input type="password" value={nouveau} onChange={(e) => setNouveau(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Confirmer</label>
          <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
        </div>
        {erreur && <p className="error-msg" style={{ gridColumn: "1 / -1" }}>{erreur}</p>}
        {message && <p className="success-msg" style={{ gridColumn: "1 / -1" }}>{message}</p>}
        <div style={{ gridColumn: "1 / -1" }}>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Enregistrement…" : "Modifier le mot de passe"}
          </button>
        </div>
      </form>
    </div>
  );
}
