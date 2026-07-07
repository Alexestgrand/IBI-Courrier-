import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, downloadPdf, downloadPiece, previewPiece, printPdf, printPiece } from "../api/client";
import AlerteErreur from "../components/AlerteErreur";
import { usePageTitle } from "../hooks/usePageTitle";
import { useToast } from "../context/ToastContext";
import { BadgeStatut, formatDate, formatTaille, LIBELLES_STATUT } from "../utils";

const MODIFIABLE = ["en_attente", "transmis"];

const CONFIRMATION_STATUT = {
  rejete: "Confirmer le rejet de ce courrier ? Cette action est difficilement réversible.",
  archive: "Archiver ce courrier ?",
};

const ICONS = {
  eye: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ),
  print: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="6 9 6 2 18 2 18 9" />
      <path d="M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2" />
      <rect x="6" y="14" width="12" height="8" />
    </svg>
  ),
  download: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  ),
};

export default function CourrierDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [courrier, setCourrier] = useState(null);
  const [historique, setHistorique] = useState([]);
  const [observation, setObservation] = useState("");
  const [erreur, setErreur] = useState("");
  const [loading, setLoading] = useState(false);
  const [edition, setEdition] = useState(false);
  const [form, setForm] = useState({});
  const [chargeLoading, setChargeLoading] = useState(true);
  const [chargeErreur, setChargeErreur] = useState("");
  const [confirmationStatut, setConfirmationStatut] = useState(null);
  const [confirmationSuppression, setConfirmationSuppression] = useState(false);

  usePageTitle(courrier ? `Courrier ${courrier.numero}` : "Courrier");

  const charger = () => {
    setChargeLoading(true);
    setChargeErreur("");
    Promise.all([api.courrier(id), api.historique(id)])
      .then(([c, h]) => {
        setCourrier(c);
        setHistorique(h);
        setForm({
          expediteur: c.expediteur || "",
          objet: c.objet || "",
          service_destinataire: c.service_destinataire || "",
          date_reception: c.date_reception || "",
          reference_document: c.reference_document || "",
          urgence: c.urgence || "normal",
          observations: c.observations || "",
          destinataire: c.destinataire || "",
          adresse_destinataire: c.adresse_destinataire || "",
          service_emetteur: c.service_emetteur || "",
          corps_courrier: c.corps_courrier || "",
        });
      })
      .catch((err) => {
        setCourrier(null);
        setChargeErreur(err.message || "Impossible de charger le courrier.");
      })
      .finally(() => setChargeLoading(false));
  };

  useEffect(() => {
    charger();
  }, [id]);

  const demanderChangementStatut = (s) => {
    if (CONFIRMATION_STATUT[s]) {
      setConfirmationStatut(s);
    } else {
      changerStatut(s);
    }
  };

  const changerStatut = async (nouveau_statut) => {
    setConfirmationStatut(null);
    setErreur("");
    setLoading(true);
    try {
      const c = await api.changerStatut(id, nouveau_statut, observation || null);
      setCourrier(c);
      setObservation("");
      const h = await api.historique(id);
      setHistorique(h);
      toast("Statut mis à jour.", "success");
    } catch (err) {
      setErreur(err.message);
      toast(err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  const sauvegarder = async () => {
    setErreur("");
    setLoading(true);
    try {
      const c = await api.modifierCourrier(id, form);
      setCourrier(c);
      setEdition(false);
      toast("Courrier enregistré.", "success");
    } catch (err) {
      setErreur(err.message);
      toast(err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  const signerPdf = async () => {
    setLoading(true);
    try {
      const c = await api.signerCourrier(id);
      setCourrier(c);
      toast("Courrier signé — PDF mis à jour.", "success");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  const supprimerCourrier = async () => {
    if (!courrier) return;
    const retour =
      courrier.type === "sortant" ? "/courriers/sortants" : "/courriers/entrants";
    setLoading(true);
    try {
      await api.supprimerCourrier(id);
      toast("Courrier supprimé.", "success");
      navigate(retour);
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setLoading(false);
      setConfirmationSuppression(false);
    }
  };

  if (chargeLoading) return <p className="loading-text">Chargement…</p>;
  if (chargeErreur) {
    return (
      <div>
        <AlerteErreur message={chargeErreur} onRetry={charger} />
        <Link to="/courriers/entrants" className="page-back">
          ← Retour à la liste
        </Link>
      </div>
    );
  }
  if (!courrier) return null;

  const listeRetour =
    courrier.type === "sortant" ? "/courriers/sortants" : "/courriers/entrants";
  const peutModifier = MODIFIABLE.includes(courrier.statut);

  return (
    <div>
      <Link to={listeRetour} className="page-back">
        ← Retour à la liste
      </Link>

      <div className="detail-header">
        <h2 className="page-title">{courrier.numero}</h2>
        <div className="actions-row" style={{ marginTop: 0 }}>
          {courrier.type === "sortant" && (
            <>
              <button
                className="btn btn-secondary"
                onClick={() =>
                  downloadPdf(courrier.id, courrier.numero).catch((e) =>
                    toast(e.message, "error")
                  )
                }
              >
                Télécharger PDF
              </button>
              <button
                className="btn btn-secondary"
                onClick={() =>
                  printPdf(courrier.id, courrier.numero).catch((e) =>
                    toast(e.message, "error")
                  )
                }
              >
                Imprimer PDF
              </button>
              {courrier.peut_signer && (
                <button
                  className="btn btn-primary"
                  type="button"
                  disabled={loading}
                  onClick={signerPdf}
                >
                  Signer le PDF
                </button>
              )}
            </>
          )}
          {peutModifier && !edition && (
            <button className="btn btn-secondary" onClick={() => setEdition(true)}>
              Modifier
            </button>
          )}
          {courrier.peut_supprimer && !edition && (
            <button
              type="button"
              className="btn btn-danger"
              disabled={loading || confirmationSuppression}
              onClick={() => setConfirmationSuppression(true)}
            >
              Supprimer
            </button>
          )}
        </div>
      </div>

      {confirmationSuppression && (
        <div className="inline-confirm" style={{ marginBottom: "1rem" }}>
          <p>
            Supprimer définitivement le courrier <strong>{courrier.numero}</strong> ?
            Les pièces jointes seront effacées. Cette action est irréversible.
          </p>
          <div className="inline-confirm__actions">
            <button
              type="button"
              className="btn btn-danger btn-sm"
              onClick={supprimerCourrier}
              disabled={loading}
            >
              Confirmer la suppression
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => setConfirmationSuppression(false)}
              disabled={loading}
            >
              Annuler
            </button>
          </div>
        </div>
      )}

      <div className="panel">
        <div className="detail-meta">
          <BadgeStatut statut={courrier.statut} />
          <span className="text-secondary">
            {courrier.entite_nom} — {courrier.type === "entrant" ? "Entrant" : "Sortant"}
          </span>
          {courrier.signe_par_nom && (
            <span className="text-secondary">
              Signé par {courrier.signe_par_nom}
              {courrier.signe_le ? ` — ${formatDate(courrier.signe_le)}` : ""}
            </span>
          )}
          {courrier.createur_nom && (
            <span className="text-secondary">Créé par {courrier.createur_nom}</span>
          )}
        </div>

        {edition ? (
          <div className="form-grid">
            {courrier.type === "entrant" ? (
              <>
                <div className="form-group">
                  <label>Expéditeur</label>
                  <input value={form.expediteur} onChange={(e) => setForm({ ...form, expediteur: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Service destinataire</label>
                  <input value={form.service_destinataire} onChange={(e) => setForm({ ...form, service_destinataire: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Date réception</label>
                  <input value={form.date_reception} onChange={(e) => setForm({ ...form, date_reception: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Référence</label>
                  <input value={form.reference_document} onChange={(e) => setForm({ ...form, reference_document: e.target.value })} />
                </div>
              </>
            ) : (
              <>
                <div className="form-group">
                  <label>Destinataire</label>
                  <input value={form.destinataire} onChange={(e) => setForm({ ...form, destinataire: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Service émetteur</label>
                  <input value={form.service_emetteur} onChange={(e) => setForm({ ...form, service_emetteur: e.target.value })} />
                </div>
                <div className="form-group" style={{ gridColumn: "1 / -1" }}>
                  <label>Adresse</label>
                  <textarea value={form.adresse_destinataire} onChange={(e) => setForm({ ...form, adresse_destinataire: e.target.value })} rows={2} />
                </div>
                <div className="form-group" style={{ gridColumn: "1 / -1" }}>
                  <label>Corps</label>
                  <textarea value={form.corps_courrier} onChange={(e) => setForm({ ...form, corps_courrier: e.target.value })} rows={6} />
                </div>
              </>
            )}
            <div className="form-group">
              <label>Objet</label>
              <input value={form.objet} onChange={(e) => setForm({ ...form, objet: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Urgence</label>
              <input value={form.urgence} onChange={(e) => setForm({ ...form, urgence: e.target.value })} />
            </div>
            <div className="form-group" style={{ gridColumn: "1 / -1" }}>
              <label>Observations</label>
              <textarea value={form.observations} onChange={(e) => setForm({ ...form, observations: e.target.value })} rows={2} />
            </div>
            <div className="actions-row" style={{ gridColumn: "1 / -1" }}>
              <button className="btn btn-primary" onClick={sauvegarder} disabled={loading}>
                Enregistrer
              </button>
              <button className="btn btn-secondary" onClick={() => setEdition(false)}>
                Annuler
              </button>
            </div>
          </div>
        ) : (
          <dl className="detail-grid">
            {courrier.type === "entrant" ? (
              <>
                <dt>Expéditeur</dt>
                <dd>{courrier.expediteur}</dd>
                <dt>Service destinataire</dt>
                <dd>{courrier.service_destinataire}</dd>
                <dt>Date réception</dt>
                <dd>{courrier.date_reception || "—"}</dd>
                <dt>Référence</dt>
                <dd>{courrier.reference_document || "—"}</dd>
              </>
            ) : (
              <>
                <dt>Destinataire</dt>
                <dd>{courrier.destinataire}</dd>
                <dt>Adresse</dt>
                <dd>{courrier.adresse_destinataire || "—"}</dd>
                <dt>Service émetteur</dt>
                <dd>{courrier.service_emetteur}</dd>
                <dt>Corps</dt>
                <dd style={{ whiteSpace: "pre-wrap" }}>{courrier.corps_courrier || "—"}</dd>
              </>
            )}
            <dt>Objet</dt>
            <dd>{courrier.objet}</dd>
            <dt>Urgence</dt>
            <dd>{courrier.urgence}</dd>
            <dt>Observations</dt>
            <dd>{courrier.observations || "—"}</dd>
          </dl>
        )}
      </div>

      {courrier.pieces_jointes?.length > 0 && (
        <div className="panel">
          <h3 className="panel__title">Pièces jointes ({courrier.pieces_jointes.length})</h3>
          <ul className="file-list">
            {courrier.pieces_jointes.map((pj) => (
              <li key={pj.id}>
                <span>
                  {pj.nom_original}{" "}
                  <span className="text-muted">({formatTaille(pj.taille_octets)})</span>
                </span>
                <div className="file-actions">
                  <button
                    className="btn-icon"
                    type="button"
                    title="Aperçu"
                    onClick={() => previewPiece(pj.id).catch((e) => toast(e.message, "error"))}
                  >
                    {ICONS.eye}
                  </button>
                  <button
                    className="btn-icon"
                    type="button"
                    title="Imprimer"
                    onClick={() => printPiece(pj.id).catch((e) => toast(e.message, "error"))}
                  >
                    {ICONS.print}
                  </button>
                  <button
                    className="btn-icon"
                    type="button"
                    title="Télécharger"
                    onClick={() => downloadPiece(pj.id, pj.nom_original).catch((e) => toast(e.message, "error"))}
                  >
                    {ICONS.download}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {courrier.statuts_possibles?.length > 0 && (
        <div className="panel">
          <h3 className="panel__title">Changer le statut</h3>
          <div className="form-group">
            <label>Observation (optionnel)</label>
            <textarea
              value={observation}
              onChange={(e) => setObservation(e.target.value)}
              rows={2}
              placeholder="Ajouter une note ou un motif…"
            />
          </div>
          {erreur && <p className="error-msg">{erreur}</p>}
          {confirmationStatut && (
            <div className="inline-confirm">
              <p>{CONFIRMATION_STATUT[confirmationStatut]}</p>
              <div className="inline-confirm__actions">
                <button
                  type="button"
                  className="btn btn-danger btn-sm"
                  onClick={() => changerStatut(confirmationStatut)}
                  disabled={loading}
                >
                  Confirmer
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setConfirmationStatut(null)}
                >
                  Annuler
                </button>
              </div>
            </div>
          )}
          <div className="statut-actions">
            {courrier.statuts_possibles.map((s) => (
              <button
                key={s}
                type="button"
                className={`btn ${s === "rejete" ? "btn-danger" : "btn-primary"}`}
                disabled={loading || confirmationStatut === s}
                aria-label={`Passer au statut ${LIBELLES_STATUT[s] || s}`}
                onClick={() => demanderChangementStatut(s)}
              >
                {LIBELLES_STATUT[s] || s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="panel">
        <h3 className="panel__title">Historique</h3>
        {historique.length === 0 ? (
          <p className="text-muted">Aucun historique.</p>
        ) : (
          <div className="historique-timeline">
            {historique.map((h) => (
              <div key={h.id} className="historique-item">
                <div className="historique-item__statut">
                  {h.ancien_statut
                    ? `${LIBELLES_STATUT[h.ancien_statut] || h.ancien_statut} → ${LIBELLES_STATUT[h.nouveau_statut] || h.nouveau_statut}`
                    : LIBELLES_STATUT[h.nouveau_statut] || h.nouveau_statut}
                </div>
                {h.observation && (
                  <div className="historique-item__obs">{h.observation}</div>
                )}
                <div className="historique-item__meta">
                  {h.utilisateur_nom || "—"} · {formatDate(h.date)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
