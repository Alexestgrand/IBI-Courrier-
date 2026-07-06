import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

const URGENCES = [
  { label: "Normal", value: "normal" },
  { label: "Urgent", value: "urgent" },
  { label: "Très urgent", value: "très urgent" },
];

export default function NouveauSortant() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [entites, setEntites] = useState([]);
  const [services, setServices] = useState([]);
  const [mode, setMode] = useState("saisie");
  const [pdfScanne, setPdfScanne] = useState(null);
  const [erreur, setErreur] = useState("");
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    entite_id: "",
    destinataire: "",
    objet: "",
    service_emetteur: "",
    adresse_destinataire: "",
    urgence: "normal",
    observations: "",
    corps_courrier: "",
  });

  useEffect(() => {
    Promise.all([api.entites(), api.services()]).then(([e, s]) => {
      setEntites(e);
      setServices(s);
      if (e.length) setForm((f) => ({ ...f, entite_id: String(e[0].id) }));
    });
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErreur("");
    setLoading(true);

    const fd = new FormData();
    Object.entries(form).forEach(([k, v]) => {
      if (v) fd.append(k, v);
    });
    if (mode === "import" && pdfScanne) {
      fd.append("pdf_scanne", pdfScanne);
    }

    try {
      const courrier = await api.creerCourrierSortant(fd);
      navigate(`/courriers/${courrier.id}`);
    } catch (err) {
      setErreur(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="page-title">Nouveau courrier sortant</h2>

      <form onSubmit={handleSubmit} className="card glass-inner form-grid">
        <div className="form-group">
          <label>Mode de création</label>
          <div className="actions-row">
            <button
              type="button"
              className={`btn ${mode === "saisie" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setMode("saisie")}
            >
              Saisie + PDF auto
            </button>
            <button
              type="button"
              className={`btn ${mode === "import" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setMode("import")}
            >
              Importer PDF scanné
            </button>
          </div>
        </div>

        <div className="form-group">
          <label>Filiale *</label>
          <select
            value={form.entite_id}
            onChange={(e) => setForm({ ...form, entite_id: e.target.value })}
            required
          >
            {entites.map((e) => (
              <option key={e.id} value={e.id}>
                {e.nom}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Destinataire *</label>
          <input
            value={form.destinataire}
            onChange={(e) => setForm({ ...form, destinataire: e.target.value })}
            required
          />
        </div>

        <div className="form-group">
          <label>Adresse destinataire</label>
          <textarea
            value={form.adresse_destinataire}
            onChange={(e) => setForm({ ...form, adresse_destinataire: e.target.value })}
            rows={2}
          />
        </div>

        <div className="form-group">
          <label>Objet *</label>
          <input
            value={form.objet}
            onChange={(e) => setForm({ ...form, objet: e.target.value })}
            required
          />
        </div>

        <div className="form-group">
          <label>Service émetteur *</label>
          <select
            value={form.service_emetteur}
            onChange={(e) => setForm({ ...form, service_emetteur: e.target.value })}
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

        {mode === "saisie" ? (
          <div className="form-group" style={{ gridColumn: "1 / -1" }}>
            <label>Corps du courrier *</label>
            <textarea
              value={form.corps_courrier}
              onChange={(e) => setForm({ ...form, corps_courrier: e.target.value })}
              rows={10}
              required={mode === "saisie"}
            />
          </div>
        ) : (
          <div className="form-group" style={{ gridColumn: "1 / -1" }}>
            <label>PDF scanné *</label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={(e) => setPdfScanne(e.target.files?.[0] || null)}
              required
            />
            {pdfScanne && <p>{pdfScanne.name}</p>}
          </div>
        )}

        <div className="form-group" style={{ gridColumn: "1 / -1" }}>
          <label>Observations</label>
          <textarea
            value={form.observations}
            onChange={(e) => setForm({ ...form, observations: e.target.value })}
            rows={2}
          />
        </div>

        {erreur && (
          <p className="error-msg" style={{ gridColumn: "1 / -1" }}>
            {erreur}
          </p>
        )}

        <div className="actions-row" style={{ gridColumn: "1 / -1" }}>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Enregistrement…" : "Enregistrer"}
          </button>
        </div>
      </form>
    </div>
  );
}
