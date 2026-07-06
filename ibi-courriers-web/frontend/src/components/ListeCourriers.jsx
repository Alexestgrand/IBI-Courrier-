import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import AlerteErreur from "./AlerteErreur";
import Pagination from "./Pagination";
import { useAuth } from "../context/AuthContext";
import { useDebounce } from "../hooks/useDebounce";
import { usePageTitle } from "../hooks/usePageTitle";
import { BadgeStatut, FILTRES_STATUT, formatDate, servicePourRole } from "../utils";

const PAGE_SIZE = 25;

const CONFIG = {
  entrant: {
    title: "Courriers entrants",
    nouveauTo: "/courriers/nouveau",
    nouveauLabel: "Nouveau entrant",
    emptyMessage: "Aucun courrier trouvé.",
    emptyCta: { to: "/courriers/nouveau", label: "Créer un courrier entrant" },
    fetch: (params) => api.courriersEntrants(params),
    columns: [
      { key: "numero", label: "Numéro" },
      { key: "entite_nom", label: "Filiale" },
      { key: "expediteur", label: "Expéditeur" },
      { key: "objet", label: "Objet" },
      { key: "service_destinataire", label: "Service" },
      { key: "statut", label: "Statut", badge: true },
      { key: "nb_pieces_jointes", label: "PJ", format: (v) => v || "—" },
      { key: "created_at", label: "Date", date: true },
    ],
  },
  sortant: {
    title: "Courriers sortants",
    nouveauTo: "/courriers/sortant/nouveau",
    nouveauLabel: "Nouveau sortant",
    emptyMessage: "Aucun courrier sortant.",
    emptyCta: { to: "/courriers/sortant/nouveau", label: "Créer un courrier sortant" },
    fetch: (params) => api.courriersSortants(params),
    columns: [
      { key: "numero", label: "N°" },
      { key: "entite_nom", label: "Filiale" },
      { key: "destinataire", label: "Destinataire" },
      { key: "objet", label: "Objet" },
      { key: "service_emetteur", label: "Service" },
      { key: "statut", label: "Statut", badge: true },
      { key: "created_at", label: "Date", date: true },
    ],
  },
};

function cellule(c, col) {
  const valeur = c[col.key];
  if (col.key === "numero") {
    return <Link to={`/courriers/${c.id}`}>{c.numero}</Link>;
  }
  if (col.badge) return <BadgeStatut statut={valeur} />;
  if (col.date) return formatDate(valeur);
  if (col.format) return col.format(valeur);
  return valeur ?? "—";
}

export default function ListeCourriers({ type }) {
  const cfg = CONFIG[type];
  usePageTitle(cfg.title);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const aUnService = Boolean(servicePourRole(user?.role));
  const [courriers, setCourriers] = useState([]);
  const [meta, setMeta] = useState({ page: 1, pages: 1, total: 0 });
  const [entites, setEntites] = useState([]);
  const [statut, setStatut] = useState(searchParams.get("statut") || "");
  const [filtreUrgents, setFiltreUrgents] = useState(searchParams.get("urgents") === "1");
  const [entiteId, setEntiteId] = useState("");
  const [recherche, setRecherche] = useState("");
  const [monService, setMonService] = useState(false);
  const [monServiceInit, setMonServiceInit] = useState(false);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [erreur, setErreur] = useState("");

  const rechercheDebounced = useDebounce(recherche, 300);

  useEffect(() => {
    const controller = new AbortController();
    api.entites(controller.signal)
      .then((data) => setEntites(data))
      .catch((err) => {
        if (err.name !== "AbortError") setEntites([]);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!monServiceInit && aUnService) {
      setMonService(true);
      setMonServiceInit(true);
    }
  }, [aUnService, monServiceInit]);

  useEffect(() => {
    setStatut(searchParams.get("statut") || "");
    setFiltreUrgents(searchParams.get("urgents") === "1");
    setPage(1);
  }, [searchParams]);

  useEffect(() => {
    setPage(1);
  }, [statut, entiteId, rechercheDebounced, monService, filtreUrgents]);

  const chargerListe = () => {
    const controller = new AbortController();
    setLoading(true);
    setErreur("");
    return cfg
      .fetch(
        {
          statut: statut || undefined,
          entite_id: entiteId || undefined,
          recherche: rechercheDebounced || undefined,
          mon_service: monService || undefined,
          urgents: filtreUrgents && type === "entrant" ? true : undefined,
          page,
          page_size: PAGE_SIZE,
        },
        controller.signal,
      )
      .then((data) => {
        setCourriers(data.items);
        setMeta({ page: data.page, pages: data.pages, total: data.total });
      })
      .catch((err) => {
        if (err.name === "AbortError") return;
        setErreur(err.message || "Impossible de charger les courriers.");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setErreur("");
    cfg
      .fetch(
        {
          statut: statut || undefined,
          entite_id: entiteId || undefined,
          recherche: rechercheDebounced || undefined,
          mon_service: monService || undefined,
          urgents: filtreUrgents && type === "entrant" ? true : undefined,
          page,
          page_size: PAGE_SIZE,
        },
        controller.signal,
      )
      .then((data) => {
        setCourriers(data.items);
        setMeta({ page: data.page, pages: data.pages, total: data.total });
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          setErreur(err.message || "Impossible de charger les courriers.");
        }
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [type, statut, entiteId, rechercheDebounced, monService, filtreUrgents, page]);

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">{cfg.title}</h2>
        <Link to={cfg.nouveauTo} className="btn btn-primary">
          {cfg.nouveauLabel}
        </Link>
      </div>

      {filtreUrgents && type === "entrant" && (
        <p className="info-banner" style={{ marginBottom: "1rem" }}>
          Affichage des courriers urgents actifs uniquement.
        </p>
      )}

      <div className="toolbar">
        <input
          type="search"
          placeholder="Rechercher…"
          value={recherche}
          onChange={(e) => setRecherche(e.target.value)}
          aria-label="Rechercher dans les courriers"
        />
        <select
          value={statut}
          onChange={(e) => setStatut(e.target.value)}
          aria-label="Filtrer par statut"
        >
          {FILTRES_STATUT.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>
        <select
          value={entiteId}
          onChange={(e) => setEntiteId(e.target.value)}
          aria-label="Filtrer par filiale"
        >
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

      <AlerteErreur message={erreur} onRetry={chargerListe} />

      <div className="panel table-wrap">
        {loading ? (
          <p className="loading-text" role="status" aria-live="polite">
            Chargement des courriers…
          </p>
        ) : erreur ? null : courriers.length === 0 ? (
          <div className="empty-state">
            <p>{cfg.emptyMessage}</p>
            <Link to={cfg.emptyCta.to} className="btn btn-primary" style={{ marginTop: "0.75rem" }}>
              {cfg.emptyCta.label}
            </Link>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                {cfg.columns.map((col) => (
                  <th key={col.key} scope="col">
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {courriers.map((c) => (
                <tr
                  key={c.id}
                  className="table-row--clickable"
                  onClick={(e) => {
                    if (e.target.closest("a") || e.target.closest("button")) return;
                    navigate(`/courriers/${c.id}`);
                  }}
                >
                  {cfg.columns.map((col) => (
                    <td key={col.key}>{cellule(c, col)}</td>
                  ))}
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
