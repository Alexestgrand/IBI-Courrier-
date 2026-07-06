import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, exportRecherchePdf } from "../api/client";
import { BadgeStatut, formatDate } from "../utils";

const FILTRES_STATUT = [
  { label: "Tous", value: "" },
  { label: "En attente", value: "en_attente" },
  { label: "Transmis", value: "transmis" },
  { label: "Validé", value: "valide" },
  { label: "Rejeté", value: "rejete" },
  { label: "Archivé", value: "archive" },
];

const TYPES = [
  { label: "Tous", value: "" },
  { label: "Entrants", value: "entrant" },
  { label: "Sortants", value: "sortant" },
];

const URGENCES = [
  { label: "Toutes", value: "" },
  { label: "Normal", value: "normal" },
  { label: "Urgent", value: "urgent" },
  { label: "Très urgent", value: "très urgent" },
];

export default function Recherche() {
  const [entites, setEntites] = useState([]);
  const [services, setServices] = useState([]);
  const [resultats, setResultats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [erreur, setErreur] = useState("");
  const [derniersParams, setDerniersParams] = useState({});

  const [filtres, setFiltres] = useState({
    mot_cle: "",
    type_courrier: "",
    statut: "",
    service: "",
    urgence: "",
    entite_id: "",
    date_debut: "",
    date_fin: "",
  });

  useEffect(() => {
    Promise.all([api.entites(), api.services()]).then(([e, s]) => {
      setEntites(e);
      setServices(s);
    });
  }, []);

  const preparerParams = () => {
    const params = { ...filtres };
    if (params.date_debut && params.date_debut.includes("-")) {
      const [y, m, d] = params.date_debut.split("-");
      params.date_debut = `${d}/${m}/${y}`;
    }
    if (params.date_fin && params.date_fin.includes("-")) {
      const [y, m, d] = params.date_fin.split("-");
      params.date_fin = `${d}/${m}/${y}`;
    }
    return params;
  };

  const lancer = async () => {
    setErreur("");
    setLoading(true);
    try {
      const params = preparerParams();
      const data = await api.recherche(params);
      setResultats(data);
      setDerniersParams(params);
    } catch (err) {
      setErreur(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="page-title">Recherche avancée</h2>

      <div className="card glass-inner form-grid">
        <div className="form-group">
          <label>Mot-clé</label>
          <input
            value={filtres.mot_cle}
            onChange={(e) => setFiltres({ ...filtres, mot_cle: e.target.value })}
            placeholder="N°, objet, expéditeur, destinataire…"
          />
        </div>
        <div className="form-group">
          <label>Type</label>
          <select
            value={filtres.type_courrier}
            onChange={(e) => setFiltres({ ...filtres, type_courrier: e.target.value })}
          >
            {TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>Statut</label>
          <select
            value={filtres.statut}
            onChange={(e) => setFiltres({ ...filtres, statut: e.target.value })}
          >
            {FILTRES_STATUT.map((f) => (
              <option key={f.value} value={f.value}>
                {f.label}
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>Service</label>
          <select
            value={filtres.service}
            onChange={(e) => setFiltres({ ...filtres, service: e.target.value })}
          >
            <option value="">Tous</option>
            {services.map((s) => (
              <option key={s.id} value={s.nom}>
                {s.nom}
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>Urgence</label>
          <select
            value={filtres.urgence}
            onChange={(e) => setFiltres({ ...filtres, urgence: e.target.value })}
          >
            {URGENCES.map((u) => (
              <option key={u.value} value={u.value}>
                {u.label}
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>Filiale</label>
          <select
            value={filtres.entite_id}
            onChange={(e) => setFiltres({ ...filtres, entite_id: e.target.value })}
          >
            <option value="">Toutes</option>
            {entites.map((e) => (
              <option key={e.id} value={e.id}>
                {e.nom}
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>Date du</label>
          <input
            type="date"
            value={filtres.date_debut}
            onChange={(e) => setFiltres({ ...filtres, date_debut: e.target.value })}
          />
        </div>
        <div className="form-group">
          <label>Date au</label>
          <input
            type="date"
            value={filtres.date_fin}
            onChange={(e) => setFiltres({ ...filtres, date_fin: e.target.value })}
          />
        </div>
        <div className="actions-row" style={{ gridColumn: "1 / -1" }}>
          <button className="btn btn-primary" onClick={lancer} disabled={loading}>
            {loading ? "Recherche…" : "Rechercher"}
          </button>
          {resultats.length > 0 && (
            <button
              className="btn btn-secondary"
              type="button"
              onClick={() => exportRecherchePdf(derniersParams).catch((e) => alert(e.message))}
            >
              Exporter PDF
            </button>
          )}
        </div>
        {erreur && (
          <p className="error-msg" style={{ gridColumn: "1 / -1" }}>
            {erreur}
          </p>
        )}
      </div>

      <div className="card glass-inner" style={{ marginTop: "1rem", overflowX: "auto" }}>
        <p style={{ marginBottom: "0.75rem", color: "var(--texte-secondaire)" }}>
          {resultats.length} résultat(s)
        </p>
        {resultats.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                <th>N°</th>
                <th>Type</th>
                <th>Contact</th>
                <th>Objet</th>
                <th>Service</th>
                <th>Urgence</th>
                <th>Statut</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {resultats.map((c) => (
                <tr key={c.id}>
                  <td>
                    <Link to={`/courriers/${c.id}`}>{c.numero}</Link>
                  </td>
                  <td>{c.type === "entrant" ? "Entrant" : "Sortant"}</td>
                  <td>{c.type === "entrant" ? c.expediteur : c.destinataire}</td>
                  <td>{c.objet}</td>
                  <td>{c.service_destinataire || c.service_emetteur}</td>
                  <td>{c.urgence}</td>
                  <td>
                    <BadgeStatut statut={c.statut} />
                  </td>
                  <td>{formatDate(c.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
