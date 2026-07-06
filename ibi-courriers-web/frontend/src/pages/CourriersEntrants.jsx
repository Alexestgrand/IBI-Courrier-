import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import Pagination from "../components/Pagination";
import { useDebounce } from "../hooks/useDebounce";
import { BadgeStatut, formatDate } from "../utils";

const FILTRES_STATUT = [
  { label: "Tous", value: "" },
  { label: "En attente", value: "en_attente" },
  { label: "Transmis", value: "transmis" },
  { label: "Validé", value: "valide" },
  { label: "Rejeté", value: "rejete" },
  { label: "Archivé", value: "archive" },
];

const PAGE_SIZE = 25;

export default function CourriersEntrants() {
  const [courriers, setCourriers] = useState([]);
  const [meta, setMeta] = useState({ page: 1, pages: 1, total: 0 });
  const [entites, setEntites] = useState([]);
  const [statut, setStatut] = useState("");
  const [entiteId, setEntiteId] = useState("");
  const [recherche, setRecherche] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const rechercheDebounced = useDebounce(recherche, 300);

  useEffect(() => {
    api.entites().then(setEntites);
  }, []);

  useEffect(() => {
    setPage(1);
  }, [statut, entiteId, rechercheDebounced]);

  useEffect(() => {
    setLoading(true);
    api
      .courriersEntrants({
        statut: statut || undefined,
        entite_id: entiteId || undefined,
        recherche: rechercheDebounced || undefined,
        page,
        page_size: PAGE_SIZE,
      })
      .then((data) => {
        setCourriers(data.items);
        setMeta({ page: data.page, pages: data.pages, total: data.total });
      })
      .finally(() => setLoading(false));
  }, [statut, entiteId, rechercheDebounced, page]);

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Courriers entrants</h2>
        <Link to="/courriers/nouveau" className="btn btn-primary">
          Nouveau entrant
        </Link>
      </div>

      <div className="toolbar">
        <input
          type="search"
          placeholder="Rechercher…"
          value={recherche}
          onChange={(e) => setRecherche(e.target.value)}
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
      </div>

      <div className="panel table-wrap">
        {loading ? (
          <p className="loading-text">Chargement…</p>
        ) : courriers.length === 0 ? (
          <div className="empty-state">
            <p>Aucun courrier trouvé.</p>
            <Link to="/courriers/nouveau" className="btn btn-primary" style={{ marginTop: "0.75rem" }}>
              Créer un courrier entrant
            </Link>
          </div>
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

      <Pagination
        page={meta.page}
        pages={meta.pages}
        total={meta.total}
        onPageChange={setPage}
      />
    </div>
  );
}
