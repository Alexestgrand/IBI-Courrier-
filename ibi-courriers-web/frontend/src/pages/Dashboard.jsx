import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

const STAT_ICONS = [
  (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  ),
  (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  ),
  (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  ),
  (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  ),
];

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
      <h2 className="page-title">Tableau de bord</h2>

      <div className="stats-grid">
        {statItems.map((item, i) => (
          <div key={item.label} className="stat-card glass-inner">
            <div className="stat-card__icon">{STAT_ICONS[i]}</div>
            <div className="stat-card__body">
              <div className="value">{item.value}</div>
              <div className="label">{item.label}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="card glass-inner">
        <h3 className="card-title">Courriers par filiale</h3>
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
        <Link to="/courriers/nouveau" className="btn btn-primary">
          Nouveau courrier entrant
        </Link>
        <Link to="/courriers/entrants" className="btn btn-secondary">
          Voir tous les courriers
        </Link>
      </div>
    </div>
  );
}
