import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import AlerteErreur from "../components/AlerteErreur";
import { BadgeStatut, formatDate } from "../utils";

function TableCourriers({ courriers, colonnes = "standard" }) {
  if (!courriers?.length) {
    return <p className="empty-state">Aucun courrier.</p>;
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th scope="col">N°</th>
            <th scope="col">Type</th>
            {colonnes === "urgent" && <th scope="col">Urgence</th>}
            <th scope="col">Objet</th>
            <th scope="col">Statut</th>
            <th scope="col">Date</th>
          </tr>
        </thead>
        <tbody>
          {courriers.map((c) => (
            <tr key={c.id}>
              <td>
                <Link to={`/courriers/${c.id}`}>{c.numero}</Link>
              </td>
              <td>{c.type === "entrant" ? "Entrant" : "Sortant"}</td>
              {colonnes === "urgent" && <td>{c.urgence}</td>}
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
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [erreur, setErreur] = useState("");

  const charger = useCallback(() => {
    setLoading(true);
    setErreur("");
    api
      .stats()
      .then(setStats)
      .catch((err) => {
        setStats(null);
        setErreur(err.message || "Impossible de charger le tableau de bord.");
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    charger();
  }, [charger]);

  if (loading) return <p className="loading-text">Chargement…</p>;
  if (erreur) {
    return (
      <div>
        <h2 className="page-title">Tableau de bord</h2>
        <AlerteErreur message={erreur} onRetry={charger} />
      </div>
    );
  }
  if (!stats) return null;

  const statItems = [
    { value: stats.total_courriers, label: "Total courriers" },
    { value: stats.en_attente, label: "En attente" },
    { value: stats.transmis, label: "Transmis" },
    { value: stats.valides, label: "Validés" },
    { value: stats.urgents, label: "Urgents actifs" },
  ];

  const journal = stats.journal_du_jour || { date: "", recus: [], traites: [] };

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

      {stats.courriers_urgents?.length > 0 && (
        <div className="panel panel--alert">
          <h3 className="panel__title">Courriers urgents à traiter</h3>
          <TableCourriers courriers={stats.courriers_urgents} colonnes="urgent" />
        </div>
      )}

      <div className="dashboard-grid">
        <div className="panel">
          <h3 className="panel__title">
            Journal du jour — reçus ({journal.recus?.length || 0})
          </h3>
          <TableCourriers courriers={journal.recus} />
        </div>
        <div className="panel">
          <h3 className="panel__title">
            Journal du jour — traités ({journal.traites?.length || 0})
          </h3>
          <TableCourriers courriers={journal.traites} />
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="panel">
          <h3 className="panel__title">Courriers par service (mois en cours)</h3>
          {Object.keys(stats.par_service || {}).length > 0 ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Service</th>
                    <th scope="col">Nombre</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(stats.par_service).map(([nom, count]) => (
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
          ) : (
            <p className="empty-state">Aucune activité ce mois-ci.</p>
          )}
        </div>

        <div className="panel">
          <h3 className="panel__title">Courriers par filiale</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Filiale</th>
                  <th scope="col">Nombre</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats.par_entite || {}).map(([nom, count]) => (
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
      </div>

      <div className="panel">
        <h3 className="panel__title">Activité récente</h3>
        <TableCourriers courriers={stats.recents} />
      </div>
    </div>
  );
}
