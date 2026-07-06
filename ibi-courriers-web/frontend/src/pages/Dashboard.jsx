import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

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

      <div className="stats-grid">
        {statItems.map((item) => (
          <div key={item.label} className="stat-card">
            <div className="stat-card__value">{item.value}</div>
            <div className="stat-card__label">{item.label}</div>
          </div>
        ))}
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
