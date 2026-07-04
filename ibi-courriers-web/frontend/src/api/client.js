const API_BASE = import.meta.env.VITE_API_URL || "/api";

function getToken() {
  return localStorage.getItem("token");
}

export function setToken(token) {
  if (token) localStorage.setItem("token", token);
  else localStorage.removeItem("token");
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (response.status === 401) {
    setToken(null);
    window.location.href = "/login";
    throw new Error("Session expirée");
  }

  if (!response.ok) {
    let detail = "Erreur serveur";
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  login: (email, mot_de_passe) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, mot_de_passe }),
    }),

  me: () => request("/auth/me"),

  stats: () => request("/dashboard/stats"),

  entites: () => request("/entites"),

  services: () => request("/services"),

  courriersEntrants: (params = {}) => {
    const qs = new URLSearchParams();
    if (params.statut) qs.set("statut", params.statut);
    if (params.recherche) qs.set("recherche", params.recherche);
    if (params.entite_id) qs.set("entite_id", params.entite_id);
    const query = qs.toString();
    return request(`/courriers/entrants${query ? `?${query}` : ""}`);
  },

  courrier: (id) => request(`/courriers/${id}`),

  historique: (id) => request(`/courriers/${id}/historique`),

  creerCourrierEntrant: (formData) =>
    request("/courriers/entrants", { method: "POST", body: formData }),

  changerStatut: (id, nouveau_statut, observation) =>
    request(`/courriers/${id}/statut`, {
      method: "PATCH",
      body: JSON.stringify({ nouveau_statut, observation }),
    }),

  downloadUrl: (pieceId) => {
    const token = getToken();
    return `${API_BASE}/pieces-jointes/${pieceId}/download?token=${token}`;
  },
};

export function downloadPiece(pieceId, nom) {
  const token = getToken();
  fetch(`${API_BASE}/pieces-jointes/${pieceId}/download`, {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((r) => {
      if (!r.ok) throw new Error("Téléchargement impossible");
      return r.blob();
    })
    .then((blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = nom;
      a.click();
      URL.revokeObjectURL(url);
    })
    .catch((e) => alert(e.message));
}
