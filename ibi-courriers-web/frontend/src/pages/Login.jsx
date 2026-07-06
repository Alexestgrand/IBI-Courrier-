import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { usePageTitle } from "../hooks/usePageTitle";

export default function Login() {
  usePageTitle("Connexion");
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionExpiree = searchParams.get("expired") === "1";
  const [email, setEmail] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [erreur, setErreur] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      navigate(user.must_change_password ? "/profil" : "/", { replace: true });
    }
  }, [user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErreur("");
    setLoading(true);
    try {
      const me = await login(email, motDePasse);
      navigate(me.must_change_password ? "/profil" : "/", { replace: true });
    } catch (err) {
      setErreur(err.message || "Identifiants incorrects.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <a href="#login-form" className="skip-link">
        Aller au formulaire
      </a>
      <div className="login-card">
        <img src="/logo-ibi.png" alt="Groupe IBI" className="login-card__logo-img" />
        <h1>IBI Courriers</h1>
        <p className="subtitle">Gestion des courriers — Groupe IBI</p>

        {sessionExpiree && (
          <p className="info-banner" role="status">
            Votre session a expiré. Veuillez vous reconnecter.
          </p>
        )}

        <form id="login-form" onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="email">E-mail</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="username"
              autoFocus
              placeholder="vous@ibi.ci"
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Mot de passe</label>
            <input
              id="password"
              type="password"
              value={motDePasse}
              onChange={(e) => setMotDePasse(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>
          {erreur && (
            <p className="error-msg" role="alert">
              {erreur}
            </p>
          )}
          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={loading}
          >
            {loading ? "Connexion…" : "Se connecter"}
          </button>
        </form>
      </div>
    </div>
  );
}
