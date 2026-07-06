import { useState } from "react";
import { downloadRapportMensuel } from "../api/client";
import { useToast } from "../context/ToastContext";

const MOIS = [
  { value: 1, label: "Janvier" },
  { value: 2, label: "Février" },
  { value: 3, label: "Mars" },
  { value: 4, label: "Avril" },
  { value: 5, label: "Mai" },
  { value: 6, label: "Juin" },
  { value: 7, label: "Juillet" },
  { value: 8, label: "Août" },
  { value: 9, label: "Septembre" },
  { value: 10, label: "Octobre" },
  { value: 11, label: "Novembre" },
  { value: 12, label: "Décembre" },
];

export default function Rapports() {
  const { toast } = useToast();
  const now = new Date();
  const [annee, setAnnee] = useState(now.getFullYear());
  const [mois, setMois] = useState(now.getMonth() + 1);
  const [loading, setLoading] = useState(false);

  const annees = Array.from({ length: 5 }, (_, i) => now.getFullYear() - i);

  const telecharger = async () => {
    setLoading(true);
    try {
      await downloadRapportMensuel(annee, mois);
      toast("Rapport téléchargé.", "success");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Rapports</h2>
      </div>

      <div className="panel" style={{ maxWidth: 480 }}>
        <h3 className="panel__title">Rapport mensuel PDF</h3>
        <p className="panel__hint">
          Volume par service, répartition par statut et délais moyens de traitement.
        </p>

        <div className="form-row" style={{ marginTop: "1rem" }}>
          <label>
            Mois
            <select value={mois} onChange={(e) => setMois(Number(e.target.value))}>
              {MOIS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Année
            <select value={annee} onChange={(e) => setAnnee(Number(e.target.value))}>
              {annees.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </label>
        </div>

        <button
          type="button"
          className="btn btn-primary"
          style={{ marginTop: "1rem" }}
          disabled={loading}
          onClick={telecharger}
        >
          {loading ? "Génération…" : "Télécharger le PDF"}
        </button>
      </div>
    </div>
  );
}
