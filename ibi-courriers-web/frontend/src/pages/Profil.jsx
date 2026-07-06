import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { usePageTitle } from "../hooks/usePageTitle";
import { useToast } from "../context/ToastContext";
import SignaturePad from "../components/SignaturePad";

export default function Profil() {
  usePageTitle("Mon profil");
  const { user, refreshUser } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const forcePassword = user?.must_change_password || location.state?.forcePassword;

  const [ancien, setAncien] = useState("");
  const [nouveau, setNouveau] = useState("");
  const [confirm, setConfirm] = useState("");
  const [erreur, setErreur] = useState("");
  const [loading, setLoading] = useState(false);
  const [sigLoading, setSigLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErreur("");
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
      await refreshUser();
      setAncien("");
      setNouveau("");
      setConfirm("");
      toast("Mot de passe modifié avec succès.", "success");
      if (forcePassword) navigate("/", { replace: true });
    } catch (err) {
      setErreur(err.message);
    } finally {
      setLoading(false);
    }
  };

  const enregistrerSignature = async (blob) => {
    setSigLoading(true);
    try {
      await api.uploadSignature(blob);
      await refreshUser();
      toast("Signature enregistrée.", "success");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setSigLoading(false);
    }
  };

  const supprimerSignature = async () => {
    setSigLoading(true);
    try {
      await api.deleteSignature();
      await refreshUser();
      toast("Signature supprimée.", "success");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setSigLoading(false);
    }
  };

  const peutSigner = user?.role === "dg" || user?.role === "admin";

  return (
    <div>
      <h2 className="page-title" style={{ marginBottom: "1.25rem" }}>
        Mon profil
      </h2>

      {forcePassword && (
        <div className="alert-banner">
          Pour des raisons de sécurité, vous devez changer votre mot de passe avant de continuer.
        </div>
      )}

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

      {peutSigner && (
        <div className="panel" style={{ marginBottom: "1rem" }}>
          <h3 className="panel__title">Signature électronique</h3>
          <p className="panel__hint">
            Dessinez votre signature pour l&apos;apposer sur les courriers sortants validés.
          </p>
          {user?.a_signature && (
            <p className="text-secondary" style={{ marginBottom: "0.75rem" }}>
              Signature enregistrée.{" "}
              <button
                type="button"
                className="btn-link"
                onClick={supprimerSignature}
                disabled={sigLoading}
              >
                Supprimer
              </button>
            </p>
          )}
          <SignaturePad onSave={enregistrerSignature} disabled={sigLoading} />
        </div>
      )}

      <form onSubmit={handleSubmit} className="panel form-grid">
        <h3 className="panel__title" style={{ gridColumn: "1 / -1", marginBottom: 0 }}>
          Changer le mot de passe
        </h3>
        <div className="form-group">
          <label>Ancien mot de passe</label>
          <input
            type="password"
            value={ancien}
            onChange={(e) => setAncien(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label>Nouveau mot de passe</label>
          <input
            type="password"
            value={nouveau}
            onChange={(e) => setNouveau(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label>Confirmer</label>
          <input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            required
          />
        </div>
        {erreur && (
          <p className="error-msg" style={{ gridColumn: "1 / -1" }}>
            {erreur}
          </p>
        )}
        <div style={{ gridColumn: "1 / -1" }}>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Enregistrement…" : "Modifier le mot de passe"}
          </button>
        </div>
      </form>
    </div>
  );
}
