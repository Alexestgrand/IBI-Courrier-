import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import AlerteErreur from "../components/AlerteErreur";
import Pagination from "../components/Pagination";
import { BadgeStatut, formatDate } from "../utils";

const PAGE_SIZE = 25;

const ORDRE_URGENCE = { "très urgent": 0, urgent: 1, normal: 2 };

export default function AValider() {
  const [courriers, setCourriers] = useState([]);
  const [meta, setMeta] = useState({ page: 1, pages: 1, total: 0 });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [erreur, setErreur] = useState("");

  const charger = () => {
    setLoading(true);
    setErreur("");
    return api
      .courriersAValider({ page, page_size: PAGE_SIZE })
      .then((data) => {
        setCourriers(data.items);
        setMeta({ page: data.page, pages: data.pages, total: data.total });
      })
      .catch((err) => {
        setErreur(err.message || "Impossible de charger la file à valider.");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setErreur("");
    api
      .courriersAValider({ page, page_size: PAGE_SIZE })
      .then((data) => {
        if (cancelled) return;
        setCourriers(data.items);
        setMeta({ page: data.page, pages: data.pages, total: data.total });
      })
      .catch((err) => {
        if (!cancelled) {
          setErreur(err.message || "Impossible de charger la file à valider.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [page]);

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">À valider</h2>
        <p className="page-subtitle">
          Courriers transmis en attente de validation DG — triés par urgence.
        </p>
      </div>

      {meta.total > 0 && !erreur && (
        <div className="panel panel--alert" style={{ marginBottom: "1rem" }}>
          <strong>{meta.total}</strong> courrier{meta.total > 1 ? "s" : ""} en attente
          de validation
        </div>
      )}

      <AlerteErreur message={erreur} onRetry={charger} />

      <div className="panel table-wrap">
        {loading ? (
          <p className="loading-text">Chargement…</p>
        ) : erreur ? null : courriers.length === 0 ? (
          <p className="empty-state">Aucun courrier à valider.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th scope="col">Numéro</th>
                <th scope="col">Filiale</th>
                <th scope="col">Expéditeur</th>
                <th scope="col">Objet</th>
                <th scope="col">Service</th>
                <th scope="col">Urgence</th>
                <th scope="col">Date</th>
                <th scope="col">Statut</th>
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

      {!erreur && (
        <Pagination
          page={meta.page}
          pages={meta.pages}
          total={meta.total}
          onPageChange={setPage}
        />
      )}
    </div>
  );
}
