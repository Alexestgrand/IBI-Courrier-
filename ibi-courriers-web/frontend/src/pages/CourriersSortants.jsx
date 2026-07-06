import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import Pagination from "../components/Pagination";
import { useAuth } from "../context/AuthContext";
import { useDebounce } from "../hooks/useDebounce";
import { BadgeStatut, formatDate, servicePourRole } from "../utils";

const FILTRES_STATUT = [
  { label: "Tous", value: "" },
  { label: "En attente", value: "en_attente" },
  { label: "Transmis", value: "transmis" },
  { label: "Validé", value: "valide" },
  { label: "Rejeté", value: "rejete" },
  { label: "Archivé", value: "archive" },
];

const PAGE_SIZE = 25;

export default function CourriersSortants() {
  const { user } = useAuth();
  const aUnService = Boolean(servicePourRole(user?.role));
  const [courriers, setCourriers] = useState([]);
  const [meta, setMeta] = useState({ page: 1, pages: 1, total: 0 });
  const [entites, setEntites] = useState([]);
  const [statut, setStatut] = useState("");
  const [entiteId, setEntiteId] = useState("");
  const [recherche, setRecherche] = useState("");
  const [monService, setMonService] = useState(false);
  const [monServiceInit, setMonServiceInit] = useState(false);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const rechercheDebounced = useDebounce(recherche, 300);

  useEffect(() => {
    api.entites().then(setEntites);
  }, []);

  useEffect(() => {
    if (!monServiceInit && aUnService) {
      setMonService(true);
      setMonServiceInit(true);
    }
  }, [aUnService, monServiceInit]);

  useEffect(() => {
    setPage(1);
  }, [statut, entiteId, rechercheDebounced, monService]);

  useEffect(() => {
    setLoading(true);
    api
      .courriersSortants({
        statut: statut || undefined,
        entite_id: entiteId || undefined,
        recherche: rechercheDebounced || undefined,
        mon_service: monService || undefined,
        page,
        page_size: PAGE_SIZE,
      })
      .then((data) => {
        setCourriers(data.items);
        setMeta({ page: data.page, pages: data.pages, total: data.total });
      })
      .finally(() => setLoading(false));
  }, [statut, entiteId, rechercheDebounced, monService, page]);

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Courriers sortants</h2>
        <Link to="/courriers/sortant/nouveau" className="btn btn-primary">
          Nouveau sortant
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
        {aUnService && (
          <label className="toolbar-checkbox">
            <input
              type="checkbox"
              checked={monService}
              onChange={(e) => setMonService(e.target.checked)}
            />
            Mon service
          </label>
        )}
      </div>

      <div className="panel table-wrap">
        {loading ? (
          <p className="loading-text">Chargement…</p>
        ) : courriers.length === 0 ? (
          <div className="empty-state">
            <p>Aucun courrier sortant.</p>
            <Link
              to="/courriers/sortant/nouveau"
              className="btn btn-primary"
              style={{ marginTop: "0.75rem" }}
            >
              Créer un courrier sortant
            </Link>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>N°</th>
                <th>Filiale</th>
                <th>Destinataire</th>
                <th>Objet</th>
                <th>Service</th>
                <th>Statut</th>
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
                  <td>{c.destinataire}</td>
                  <td>{c.objet}</td>
                  <td>{c.service_emetteur}</td>
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

      <Pagination
        page={meta.page}
        pages={meta.pages}
        total={meta.total}
        onPageChange={setPage}
      />
    </div>
  );
}
