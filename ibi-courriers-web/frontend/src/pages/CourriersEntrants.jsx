import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { BadgeStatut, formatDate } from "../utils";

const FILTRES_STATUT = [
  { label: "Tous", value: "" },
  { label: "En attente", value: "en_attente" },
  { label: "Transmis", value: "transmis" },
  { label: "Validé", value: "valide" },
  { label: "Rejeté", value: "rejete" },
  { label: "Archivé", value: "archive" },
];

export default function CourriersEntrants() {
  const [courriers, setCourriers] = useState([]);
  const [entites, setEntites] = useState([]);
  const [statut, setStatut] = useState("");
  const [entiteId, setEntiteId] = useState("");
  const [recherche, setRecherche] = useState("");
  const [loading, setLoading] = useState(true);

  const charger = () => {
    setLoading(true);
    api
      .courriersEntrants({
        statut: statut || undefined,
        entite_id: entiteId || undefined,
        recherche: recherche || undefined,
      })
      .then(setCourriers)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    api.entites().then(setEntites);
  }, []);

  useEffect(() => {
    charger();
  }, [statut, entiteId]);

  return (
    <div>
      <h2 className="page-title">Courriers entrants</h2>

      <div className="toolbar glass-inner">
        <input
          type="search"
          placeholder="Rechercher…"
          value={recherche}
          onChange={(e) => setRecherche(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && charger()}
        />
        <select value={statut} onChange={(e) => setStatut(e.target.value)}>
          {FILTRES_STATUT.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>
        <select value={entiteId} onChange={(e) => setEntiteId(e.target.value)}>
          <option value="">Toutes les filiales</option>
          {entites.map((e) => (
            <option key={e.id} value={e.id}>
              {e.nom}
            </option>
          ))}
        </select>
        <button className="btn btn-secondary" onClick={charger}>
          Filtrer
        </button>
        <Link to="/courriers/nouveau" className="btn btn-primary">
          + Nouveau
        </Link>
      </div>

      <div className="card table-wrap glass-inner">
        {loading ? (
          <p>Chargement…</p>
        ) : courriers.length === 0 ? (
          <p style={{ color: "var(--texte-secondaire)" }}>Aucun courrier trouvé.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Numéro</th>
                <th>Filiale</th>
                <th>Expéditeur</th>
                <th>Objet</th>
                <th>Service</th>
                <th>Statut</th>
                <th>PJ</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {courriers.map((c) => (
                <tr key={c.id}>
                  <td>
                    <Link to={`/courriers/${c.id}`}>{c.numero}</Link>
                  </td>
                  <td>{c.entite_nom}</td>
                  <td>{c.expediteur}</td>
                  <td>{c.objet}</td>
                  <td>{c.service_destinataire}</td>
                  <td>
                    <BadgeStatut statut={c.statut} />
                  </td>
                  <td>{c.nb_pieces_jointes || "—"}</td>
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
