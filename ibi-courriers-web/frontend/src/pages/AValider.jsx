import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import Pagination from "../components/Pagination";
import { BadgeStatut, formatDate } from "../utils";

const PAGE_SIZE = 25;

const ORDRE_URGENCE = { "très urgent": 0, urgent: 1, normal: 2 };

export default function AValider() {
  const [courriers, setCourriers] = useState([]);
  const [meta, setMeta] = useState({ page: 1, pages: 1, total: 0 });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .courriersAValider({ page, page_size: PAGE_SIZE })
      .then((data) => {
        setCourriers(data.items);
        setMeta({ page: data.page, pages: data.pages, total: data.total });
      })
      .finally(() => setLoading(false));
  }, [page]);

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">À valider</h2>
        <p className="page-subtitle">
          Courriers transmis en attente de validation DG — triés par urgence.
        </p>
      </div>

      {meta.total > 0 && (
        <div className="panel panel--alert" style={{ marginBottom: "1rem" }}>
          <strong>{meta.total}</strong> courrier{meta.total > 1 ? "s" : ""} en attente
          de validation
        </div>
      )}

      <div className="panel table-wrap">
        {loading ? (
          <p className="loading-text">Chargement…</p>
        ) : courriers.length === 0 ? (
          <p className="empty-state">Aucun courrier à valider.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Numéro</th>
                <th>Filiale</th>
                <th>Expéditeur</th>
                <th>Objet</th>
                <th>Service</th>
                <th>Urgence</th>
                <th>Date</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {courriers.map((c) => (
                <tr
                  key={c.id}
                  className={
                    ORDRE_URGENCE[c.urgence] <= 1 ? "row-urgent" : undefined
                  }
                >
                  <td>
                    <Link to={`/courriers/${c.id}`}>{c.numero}</Link>
                  </td>
                  <td>{c.entite_nom}</td>
                  <td>{c.expediteur}</td>
                  <td>{c.objet}</td>
                  <td>{c.service_destinataire}</td>
                  <td>
                    <span className={`urgence-tag urgence-tag--${c.urgence?.replace(" ", "-")}`}>
                      {c.urgence}
                    </span>
                  </td>
                  <td>{formatDate(c.created_at)}</td>
                  <td>
                    <BadgeStatut statut={c.statut} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <Pagination
        page={meta.page}
        pages={meta.pages}
        total={meta.total}
        onPageChange={setPage}
      />
    </div>
  );
}
