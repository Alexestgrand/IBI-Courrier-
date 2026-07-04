import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, downloadPiece } from "../api/client";
import { BadgeStatut, formatDate, formatTaille } from "../utils";

const LIBELLES_STATUT = {
  en_attente: "En attente",
  transmis: "Transmis",
  valide: "Validé",
  rejete: "Rejeté",
  archive: "Archivé",
};

export default function CourrierDetail() {
  const { id } = useParams();
  const [courrier, setCourrier] = useState(null);
  const [historique, setHistorique] = useState([]);
  const [observation, setObservation] = useState("");
  const [erreur, setErreur] = useState("");
  const [loading, setLoading] = useState(false);

  const charger = () => {
    Promise.all([api.courrier(id), api.historique(id)]).then(([c, h]) => {
      setCourrier(c);
      setHistorique(h);
    });
  };

  useEffect(() => {
    charger();
  }, [id]);

  const changerStatut = async (nouveau_statut) => {
    setErreur("");
    setLoading(true);
    try {
      const c = await api.changerStatut(id, nouveau_statut, observation || null);
      setCourrier(c);
      setObservation("");
      const h = await api.historique(id);
      setHistorique(h);
    } catch (err) {
      setErreur(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!courrier) return <p>Chargement…</p>;

  return (
    <div>
      <Link to="/courriers/entrants" style={{ color: "var(--texte-secondaire)" }}>
        ← Retour à la liste
      </Link>
      <h2 className="page-title" style={{ marginTop: "0.75rem" }}>
        {courrier.numero}
      </h2>

      <div className="card glass-inner">
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1rem" }}>
          <BadgeStatut statut={courrier.statut} />
          <span style={{ color: "var(--texte-secondaire)" }}>{courrier.entite_nom}</span>
        </div>

        <dl className="detail-grid">
          <dt>Expéditeur</dt>
          <dd>{courrier.expediteur}</dd>
          <dt>Objet</dt>
          <dd>{courrier.objet}</dd>
          <dt>Service destinataire</dt>
          <dd>{courrier.service_destinataire}</dd>
          <dt>Date réception</dt>
          <dd>{courrier.date_reception || "—"}</dd>
          <dt>Référence</dt>
          <dd>{courrier.reference_document || "—"}</dd>
          <dt>Urgence</dt>
          <dd>{courrier.urgence}</dd>
          <dt>Observations</dt>
          <dd>{courrier.observations || "—"}</dd>
        </dl>
      </div>

      {courrier.pieces_jointes?.length > 0 && (
        <div className="card glass-inner">
          <h3 style={{ marginBottom: "0.75rem" }}>
            Pièces jointes ({courrier.pieces_jointes.length})
          </h3>
          <ul className="file-list">
            {courrier.pieces_jointes.map((pj) => (
              <li key={pj.id}>
                <span>
                  📎 {pj.nom_original} ({formatTaille(pj.taille_octets)})
                </span>
                <button
                  className="btn btn-secondary"
                  style={{ padding: "0.3rem 0.6rem", fontSize: "0.8rem" }}
                  onClick={() => downloadPiece(pj.id, pj.nom_original)}
                >
                  Télécharger
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {courrier.statuts_possibles?.length > 0 && (
        <div className="card glass-inner">
          <h3 style={{ marginBottom: "0.75rem" }}>Changer le statut</h3>
          <div className="form-group">
            <label>Observation (optionnel)</label>
            <textarea
              value={observation}
              onChange={(e) => setObservation(e.target.value)}
              rows={2}
            />
          </div>
          {erreur && <p className="error-msg">{erreur}</p>}
          <div className="actions-row">
            {courrier.statuts_possibles.map((s) => (
              <button
                key={s}
                className={`btn ${s === "rejete" ? "btn-danger" : "btn-primary"}`}
                disabled={loading}
                onClick={() => changerStatut(s)}
              >
                → {LIBELLES_STATUT[s] || s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="card glass-inner">
        <h3 style={{ marginBottom: "0.75rem" }}>Historique</h3>
        {historique.length === 0 ? (
          <p style={{ color: "var(--texte-secondaire)" }}>Aucun historique.</p>
        ) : (
          historique.map((h) => (
            <div key={h.id} className="historique-item">
              <strong>
                {h.ancien_statut
                  ? `${LIBELLES_STATUT[h.ancien_statut] || h.ancien_statut} → `
                  : ""}
                {LIBELLES_STATUT[h.nouveau_statut] || h.nouveau_statut}
              </strong>
              {h.observation && (
                <div style={{ color: "var(--texte-secondaire)" }}>{h.observation}</div>
              )}
              <div style={{ fontSize: "0.8rem", color: "var(--texte-secondaire)" }}>
                {h.utilisateur_nom || "—"} — {formatDate(h.date)}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
