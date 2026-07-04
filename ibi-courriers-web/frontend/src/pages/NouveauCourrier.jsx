import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { formatTaille } from "../utils";

const URGENCES = [
  { label: "Normal", value: "normal" },
  { label: "Urgent", value: "urgent" },
  { label: "Très urgent", value: "très urgent" },
];

export default function NouveauCourrier() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [entites, setEntites] = useState([]);
  const [services, setServices] = useState([]);
  const [fichiers, setFichiers] = useState([]);
  const [erreur, setErreur] = useState("");
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const [form, setForm] = useState({
    entite_id: "",
    expediteur: "",
    objet: "",
    service_destinataire: "",
    date_reception: new Date().toISOString().slice(0, 10),
    reference_document: "",
    urgence: "normal",
    observations: "",
  });

  useEffect(() => {
    Promise.all([api.entites(), api.services()]).then(([e, s]) => {
      setEntites(e);
      setServices(s);
      if (e.length) setForm((f) => ({ ...f, entite_id: String(e[0].id) }));
    });
  }, []);

  const ajouterFichiers = (fileList) => {
    const nouveaux = Array.from(fileList);
    setFichiers((prev) => {
      const existants = new Set(prev.map((f) => f.name + f.size));
      return [...prev, ...nouveaux.filter((f) => !existants.has(f.name + f.size))];
    });
  };

  const retirerFichier = (index) => {
    setFichiers((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErreur("");
    setLoading(true);

    const fd = new FormData();
    Object.entries(form).forEach(([k, v]) => {
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
    <div>
      <h2 className="page-title">Nouveau courrier entrant</h2>

      <form className="card glass-inner" onSubmit={handleSubmit} style={{ maxWidth: 720 }}>
        <div className="form-row">
          <div className="form-group">
            <label>Filiale *</label>
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
          <label>Expéditeur *</label>
          <input
            value={form.expediteur}
            onChange={(e) => setForm({ ...form, expediteur: e.target.value })}
            required
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

        <div className="form-group">
          <label>Pièces jointes (plusieurs fichiers)</label>
          <div
            className={`dropzone ${dragOver ? "dragover" : ""}`}
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
            Glisser vos fichiers ici ou cliquer pour sélectionner
            <br />
            <small>PDF, JPG, PNG, DOCX</small>
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
                    📎 {f.name} ({formatTaille(f.size)})
                  </span>
                  <button type="button" onClick={() => retirerFichier(i)}>
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {erreur && <p className="error-msg">{erreur}</p>}

        <div className="actions-row">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Enregistrement…" : "Enregistrer le courrier"}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate(-1)}
          >
            Annuler
          </button>
        </div>
      </form>
    </div>
  );
}
