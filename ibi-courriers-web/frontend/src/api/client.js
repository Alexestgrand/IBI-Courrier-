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

function buildQuery(params) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") qs.set(k, v);
  });
  const query = qs.toString();
  return query ? `?${query}` : "";
}

export const api = {
  login: (email, mot_de_passe) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, mot_de_passe }),
    }),

  me: () => request("/auth/me"),

  changePassword: (ancien_mot_de_passe, nouveau_mot_de_passe) =>
    request("/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ ancien_mot_de_passe, nouveau_mot_de_passe }),
    }),

  stats: () => request("/dashboard/stats"),

  entites: () => request("/entites"),

  services: () => request("/services"),

  courriersEntrants: (params = {}) =>
    request(`/courriers/entrants${buildQuery(params)}`),

  courriersSortants: (params = {}) =>
    request(`/courriers/sortants${buildQuery(params)}`),

  courrier: (id) => request(`/courriers/${id}`),

  historique: (id) => request(`/courriers/${id}/historique`),

  creerCourrierEntrant: (formData) =>
    request("/courriers/entrants", { method: "POST", body: formData }),

  creerCourrierSortant: (formData) =>
    request("/courriers/sortants", { method: "POST", body: formData }),

  modifierCourrier: (id, data) =>
    request(`/courriers/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  changerStatut: (id, nouveau_statut, observation) =>
    request(`/courriers/${id}/statut`, {
      method: "PATCH",
      body: JSON.stringify({ nouveau_statut, observation }),
    }),

  recherche: (params = {}) => request(`/recherche${buildQuery(params)}`),

  utilisateurs: (params = {}) => request(`/users${buildQuery(params)}`),

  creerUtilisateur: (data) =>
    request("/users", { method: "POST", body: JSON.stringify(data) }),

  modifierUtilisateur: (id, data) =>
    request(`/users/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  resetMotDePasse: (id, mot_de_passe = null) =>
    request(`/users/${id}/reset-password`, {
      method: "POST",
      body: JSON.stringify({ mot_de_passe }),
    }),

  audit: (params = {}) => request(`/audit${buildQuery(params)}`),
};

function downloadBlob(path, filename) {
  const token = getToken();
  return fetch(`${API_BASE}${path}`, {
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
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    });
}

export function downloadPiece(pieceId, nom) {
  downloadBlob(`/pieces-jointes/${pieceId}/download`, nom).catch((e) =>
    alert(e.message)
  );
}

export function downloadPdf(courrierId, numero) {
  downloadBlob(`/courriers/${courrierId}/pdf`, `${numero}.pdf`).catch((e) =>
    alert(e.message)
  );
}

export function exportRecherchePdf(filtres) {
  const qs = buildQuery(filtres);
  const date = new Date().toISOString().slice(0, 10);
  return downloadBlob(`/recherche/export-pdf${qs}`, `rapport_recherche_${date}.pdf`);
}
