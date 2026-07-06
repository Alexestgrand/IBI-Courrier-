import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useToast } from "../context/ToastContext";
import { usePageTitle } from "../hooks/usePageTitle";
import { formatTaille, URGENCES } from "../utils";

const ETAPES = [
  { id: 1, label: "Scan" },
  { id: 2, label: "Informations" },
  { id: 3, label: "Validation" },
];

const CONFIANCE_STYLES = {
  haute: "ocr-badge--high",
  moyenne: "ocr-badge--mid",
  basse: "ocr-badge--low",
};

function ApercuFichier({ fichier }) {
  const [url, setUrl] = useState(null);
  const estImage = /\.(jpe?g|png)$/i.test(fichier?.name || "");

  useEffect(() => {
    if (!fichier || !estImage) {
      setUrl(null);
      return undefined;
    }
    const objectUrl = URL.createObjectURL(fichier);
    setUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [fichier, estImage]);

  if (!fichier) {
    return (
      <div className="scan-preview scan-preview--empty">
        <p>Aucun document sélectionné</p>
      </div>
    );
  }

  if (estImage && url) {
    return (
      <div className="scan-preview">
        <img src={url} alt="Aperçu du scan" />
      </div>
    );
  }

  return (
    <div className="scan-preview scan-preview--file">
      <p className="scan-preview__name">{fichier.name}</p>
      <p className="scan-preview__meta">{formatTaille(fichier.size)}</p>
      <p className="scan-preview__hint">Aperçu PDF disponible après enregistrement.</p>
    </div>
  );
}

export default function NouveauCourrier() {
  usePageTitle("Nouveau courrier entrant");
  const navigate = useNavigate();
  const { toast } = useToast();
  const fileInputRef = useRef(null);
  const ocrEnCours = useRef(false);

  const [etape, setEtape] = useState(1);
  const [entites, setEntites] = useState([]);
  const [services, setServices] = useState([]);
  const [fichiers, setFichiers] = useState([]);
  const [fichierScan, setFichierScan] = useState(null);
  const [erreur, setErreur] = useState("");
  const [loading, setLoading] = useState(false);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [refErreur, setRefErreur] = useState("");
  const [ocrMeta, setOcrMeta] = useState(null);

  const [form, setForm] = useState({
    entite_id: "",
    type_expediteur: "externe",
    expediteur: "",
    objet: "",
    service_destinataire: "",
    date_reception: new Date().toISOString().slice(0, 10),
    reference_document: "",
    urgence: "normal",
    observations: "",
  });

  useEffect(() => {
    Promise.all([api.entites(), api.services()])
      .then(([e, s]) => {
        setEntites(e);
        setServices(s);
        if (e.length) setForm((f) => ({ ...f, entite_id: String(e[0].id) }));
      })
      .catch((err) => {
        setRefErreur(err.message || "Impossible de charger les listes déroulantes.");
      });
  }, []);

  const lancerOcr = useCallback(
    async (fichier) => {
      if (!fichier || ocrEnCours.current) return;
      ocrEnCours.current = true;
      setOcrLoading(true);
      try {
        const res = await api.ocrExtract(fichier);
        const s = res.suggestions || {};
        setOcrMeta({ confiance: res.confiance, methode: res.methode, avertissement: res.avertissement });
        setForm((f) => ({
          ...f,
          expediteur: s.expediteur || f.expediteur,
          reference_document: s.reference_document || f.reference_document,
          objet: s.objet || f.objet,
          type_expediteur: "externe",
        }));
        if (res.avertissement) toast(res.avertissement, "error");
        else toast(`Scan analysé — confiance ${res.confiance}.`, "success");
      } catch (e) {
        toast(e.message, "error");
      } finally {
        setOcrLoading(false);
        ocrEnCours.current = false;
      }
    },
    [toast],
  );

  const ajouterFichiers = (fileList) => {
    const nouveaux = Array.from(fileList);
    setFichiers((prev) => {
      const existants = new Set(prev.map((f) => f.name + f.size));
      return [...prev, ...nouveaux.filter((f) => !existants.has(f.name + f.size))];
    });

    const scan = nouveaux.find((f) => /\.(pdf|jpe?g|png)$/i.test(f.name));
    if (scan) {
      setFichierScan(scan);
      lancerOcr(scan);
    }
  };

  const retirerFichier = (index) => {
    setFichiers((prev) => {
      const next = prev.filter((_, i) => i !== index);
      const removed = prev[index];
      if (fichierScan && removed === fichierScan) {
        const autre = next.find((f) => /\.(pdf|jpe?g|png)$/i.test(f.name));
        setFichierScan(autre || null);
      }
      return next;
    });
  };

  const expediteurFinal = () => {
    if (form.type_expediteur === "interne") {
      const entite = entites.find((e) => String(e.id) === form.entite_id);
      return form.expediteur.trim() || entite?.nom || "Groupe IBI";
    }
    return form.expediteur.trim();
  };

  const peutEtapeSuivante = () => {
    if (etape === 1) return fichiers.length > 0;
    if (etape === 2) {
      return (
        form.entite_id &&
        expediteurFinal() &&
        form.objet.trim() &&
        form.service_destinataire
      );
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErreur("");
    setLoading(true);

    const fd = new FormData();
    const payload = {
      ...form,
      expediteur: expediteurFinal(),
      date_reception: form.date_reception,
    };
    Object.entries(payload).forEach(([k, v]) => {
      if (k === "type_expediteur") return;
      if (v) fd.append(k, v);
    });
    fichiers.forEach((f) => fd.append("fichiers", f));

    try {
      const courrier = await api.creerCourrierEntrant(fd);
      navigate(`/courriers/${courrier.id}`);
    } catch (err) {
      setErreur(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="wizard-page">
      <div className="page-header">
        <div>
          <h2 className="page-title">Nouveau courrier entrant</h2>
          <p className="page-subtitle">
            Déposez le scan, vérifiez les informations, puis enregistrez.
          </p>
        </div>
      </div>

      <ol className="wizard-steps" aria-label="Étapes">
        {ETAPES.map((e) => (
          <li
            key={e.id}
            className={`wizard-steps__item${etape === e.id ? " is-active" : ""}${etape > e.id ? " is-done" : ""}`}
          >
            <span className="wizard-steps__num">{e.id}</span>
            <span>{e.label}</span>
          </li>
        ))}
      </ol>

      {refErreur && <p className="error-msg">{refErreur}</p>}

      <form className="panel wizard-panel" onSubmit={handleSubmit}>
        {etape === 1 && (
          <div className="wizard-grid">
            <div>
              <h3 className="form-section__title">1. Déposer le scan</h3>
              <p className="panel__hint">
                PDF, JPG ou PNG — l&apos;analyse OCR démarre automatiquement.
              </p>
              <div
                className={`dropzone dropzone--large ${dragOver ? "dragover" : ""}`}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragOver(false);
                  ajouterFichiers(e.dataTransfer.files);
                }}
              >
                {ocrLoading ? "Analyse du scan en cours…" : "Glisser le courrier scanné ici ou cliquer"}
                <br />
                <small>PDF, JPG, PNG — qualité moyenne acceptée</small>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                hidden
                accept=".pdf,.jpg,.jpeg,.png,.docx"
                onChange={(e) => ajouterFichiers(e.target.files)}
              />
              {fichiers.length > 0 && (
                <ul className="file-list">
                  {fichiers.map((f, i) => (
                    <li key={`${f.name}-${i}`}>
                      <span>
                        {f.name} ({formatTaille(f.size)})
                        {f === fichierScan && " — scan principal"}
                      </span>
                      <button type="button" onClick={() => retirerFichier(i)}>
                        ✕
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <h3 className="form-section__title">Aperçu</h3>
              <ApercuFichier fichier={fichierScan} />
              {ocrMeta && (
                <p className={`ocr-badge ${CONFIANCE_STYLES[ocrMeta.confiance] || ""}`}>
                  OCR : confiance {ocrMeta.confiance}
                  {ocrMeta.methode ? ` (${ocrMeta.methode})` : ""}
                </p>
              )}
            </div>
          </div>
        )}

        {etape === 2 && (
          <div className="wizard-grid wizard-grid--form">
            <div className="form-section">
              <h3 className="form-section__title">Qui envoie ce courrier ?</h3>
              <p className="panel__hint">
                En général il s&apos;agit d&apos;un organisme extérieur (administration, banque, fournisseur…).
              </p>
              <div className="choice-row">
                <label className={`choice-card${form.type_expediteur === "externe" ? " is-selected" : ""}`}>
                  <input
                    type="radio"
                    name="type_expediteur"
                    value="externe"
                    checked={form.type_expediteur === "externe"}
                    onChange={() => setForm({ ...form, type_expediteur: "externe", expediteur: "" })}
                  />
                  <strong>Organisme extérieur</strong>
                  <span>Ministère, banque, client, fournisseur…</span>
                </label>
                <label className={`choice-card${form.type_expediteur === "interne" ? " is-selected" : ""}`}>
                  <input
                    type="radio"
                    name="type_expediteur"
                    value="interne"
                    checked={form.type_expediteur === "interne"}
                    onChange={() => setForm({ ...form, type_expediteur: "interne", expediteur: "" })}
                  />
                  <strong>Groupe IBI (interne)</strong>
                  <span>Filiale ou service du groupe</span>
                </label>
              </div>
              {form.type_expediteur === "externe" ? (
                <div className="form-group">
                  <label htmlFor="expediteur">Nom de l&apos;expéditeur *</label>
                  <input
                    id="expediteur"
                    value={form.expediteur}
                    onChange={(e) => setForm({ ...form, expediteur: e.target.value })}
                    placeholder="Ex. : SODECI, Ministère des Finances, Banque Atlantique…"
                    required
                  />
                </div>
              ) : (
                <div className="form-group">
                  <label htmlFor="expediteur-interne">Filiale / service émetteur *</label>
                  <select
                    id="expediteur-interne"
                    value={form.expediteur}
                    onChange={(e) => setForm({ ...form, expediteur: e.target.value })}
                    required
                  >
                    <option value="">— Choisir —</option>
                    {entites.map((ent) => (
                      <option key={ent.id} value={ent.nom}>
                        {ent.nom}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            <div className="form-section">
              <h3 className="form-section__title">Contenu du courrier</h3>
              <div className="form-row">
                <div className="form-group">
                  <label>Filiale destinataire *</label>
                  <select
                    value={form.entite_id}
                    onChange={(e) => setForm({ ...form, entite_id: e.target.value })}
                    required
                  >
                    {entites.map((ent) => (
                      <option key={ent.id} value={ent.id}>
                        {ent.nom}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Date de réception</label>
                  <input
                    type="date"
                    value={form.date_reception}
                    onChange={(e) => setForm({ ...form, date_reception: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Objet *</label>
                <input
                  value={form.objet}
                  onChange={(e) => setForm({ ...form, objet: e.target.value })}
                  required
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Service destinataire *</label>
                  <select
                    value={form.service_destinataire}
                    onChange={(e) =>
                      setForm({ ...form, service_destinataire: e.target.value })
                    }
                    required
                  >
                    <option value="">— Choisir —</option>
                    {services.map((s) => (
                      <option key={s.id} value={s.nom}>
                        {s.nom}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Urgence</label>
                  <select
                    value={form.urgence}
                    onChange={(e) => setForm({ ...form, urgence: e.target.value })}
                  >
                    {URGENCES.map((u) => (
                      <option key={u.value} value={u.value}>
                        {u.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>Référence document</label>
                <input
                  value={form.reference_document}
                  onChange={(e) =>
                    setForm({ ...form, reference_document: e.target.value })
                  }
                />
              </div>
              <div className="form-group">
                <label>Observations</label>
                <textarea
                  value={form.observations}
                  onChange={(e) => setForm({ ...form, observations: e.target.value })}
                />
              </div>
            </div>

            <div>
              <h3 className="form-section__title">Aperçu du scan</h3>
              <ApercuFichier fichier={fichierScan} />
            </div>
          </div>
        )}

        {etape === 3 && (
          <div className="recap-panel">
            <h3 className="form-section__title">Récapitulatif avant enregistrement</h3>
            <dl className="recap-list">
              <div><dt>Expéditeur</dt><dd>{expediteurFinal()}</dd></div>
              <div><dt>Type</dt><dd>{form.type_expediteur === "externe" ? "Organisme extérieur" : "Groupe IBI"}</dd></div>
              <div><dt>Objet</dt><dd>{form.objet}</dd></div>
              <div><dt>Service</dt><dd>{form.service_destinataire}</dd></div>
              <div><dt>Urgence</dt><dd>{form.urgence}</dd></div>
              <div><dt>Pièces jointes</dt><dd>{fichiers.length} fichier(s)</dd></div>
            </dl>
          </div>
        )}

        {erreur && <p className="error-msg">{erreur}</p>}

        <div className="wizard-actions">
          {etape > 1 && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setEtape((e) => e - 1)}
            >
              Étape précédente
            </button>
          )}
          {etape < 3 ? (
            <button
              type="button"
              className="btn btn-primary"
              disabled={!peutEtapeSuivante() || ocrLoading}
              onClick={() => setEtape((e) => e + 1)}
            >
              Étape suivante
            </button>
          ) : (
            <button type="submit" className="btn btn-primary btn-lg" disabled={loading}>
              {loading ? "Enregistrement…" : "Enregistrer le courrier entrant"}
            </button>
          )}
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => navigate(-1)}
          >
            Annuler
          </button>
        </div>
      </form>
    </div>
  );
}
