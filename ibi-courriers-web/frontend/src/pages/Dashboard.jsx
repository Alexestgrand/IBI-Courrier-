import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { BadgeStatut, formatDate } from "../utils";

export default function Dashboard() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.stats().then(setStats).catch(console.error);
  }, []);

  if (!stats) return <p className="loading-text">Chargement…</p>;

  const statItems = [
    { value: stats.total_courriers, label: "Total courriers" },
    { value: stats.en_attente, label: "En attente" },
    { value: stats.transmis, label: "Transmis" },
    { value: stats.valides, label: "Validés" },
    { value: stats.urgents, label: "Urgents actifs" },
  ];

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Tableau de bord</h2>
        <div className="actions-row" style={{ marginTop: 0 }}>
          <Link to="/courriers/nouveau" className="btn btn-primary">
            Nouveau entrant
          </Link>
        </div>
      </div>

      <div className="stats-grid stats-grid--5">
        {statItems.map((item) => (
          <div key={item.label} className="stat-card">
            <div className="stat-card__value">{item.value}</div>
            <div className="stat-card__label">{item.label}</div>
          </div>
        ))}
      </div>

      <div className="panel">
        <h3 className="panel__title">Courriers récents</h3>
        {stats.recents?.length > 0 ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>N°</th>
                  <th>Type</th>
                  <th>Objet</th>
                  <th>Statut</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {stats.recents.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <Link to={`/courriers/${c.id}`}>{c.numero}</Link>
                    </td>
                    <td>{c.type === "entrant" ? "Entrant" : "Sortant"}</td>
                    <td>{c.objet}</td>
                    <td>
                      <BadgeStatut statut={c.statut} />
                    </td>
                    <td>{formatDate(c.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="empty-state">Aucun courrier récent.</p>
        )}
      </div>

      <div className="panel">
        <h3 className="panel__title">Courriers par filiale</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Filiale</th>
                <th>Nombre</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(stats.par_entite).map(([nom, count]) => (
                <tr key={nom}>
                  <td>{nom}</td>
                  <td>
                    <span className="table-count">{count}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="actions-row">
        <Link to="/courriers/entrants" className="btn btn-secondary">
          Voir les entrants
        </Link>
        <Link to="/courriers/sortants" className="btn btn-secondary">
          Voir les sortants
        </Link>
      </div>
    </div>
  );
}
