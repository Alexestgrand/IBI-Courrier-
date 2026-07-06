const API_BASE = import.meta.env.VITE_API_URL || "/api";

const fetchOptions = { credentials: "include" };

function doitRedirigerSur401(path) {
  if (path === "/auth/login" || path.startsWith("/auth/login?")) return false;
  if (window.location.pathname === "/login") return false;
  return true;
}

function redirigerSessionExpiree() {
  if (window.location.pathname === "/login") return;
  const params = new URLSearchParams({ expired: "1" });
  window.location.replace(`/login?${params.toString()}`);
}

async function request(path, options = {}) {
  const { signal, ...rest } = options;
  const headers = { ...(rest.headers || {}) };

  if (!(rest.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...fetchOptions,
    ...rest,
    headers,
    signal,
  });

  if (response.status === 401) {
    if (doitRedirigerSur401(path)) {
      redirigerSessionExpiree();
    }
    throw new Error("Session expirée");
  }

  if (response.status === 403) {
    let detail = "";
    try {
      const data = await response.json();
      detail = typeof data.detail === "string" ? data.detail : "";
    } catch {
      /* ignore */
    }
    if (detail.includes("changer votre mot de passe")) {
      window.location.href = "/profil";
      throw new Error(detail);
    }
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
    if (v === undefined || v === null || v === "") return;
    if (typeof v === "boolean") {
      if (v) qs.set(k, "true");
      return;
    }
    qs.set(k, v);
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

  logout: () => request("/auth/logout", { method: "POST" }),

  me: () => request("/auth/me"),

  changePassword: (ancien_mot_de_passe, nouveau_mot_de_passe) =>
    request("/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ ancien_mot_de_passe, nouveau_mot_de_passe }),
    }),

  stats: (signal) => request("/dashboard/stats", { signal }),

  entites: (signal) => request("/entites", { signal }),

  services: (signal) => request("/services", { signal }),

  courriersEntrants: (params = {}, signal) => {
    const qs = buildQuery(params);
    return request(`/courriers/entrants${qs}`, { signal });
  },

  courriersSortants: (params = {}, signal) =>
    request(`/courriers/sortants${buildQuery(params)}`, { signal }),

  courrier: (id, signal) => request(`/courriers/${id}`, { signal }),

  historique: (id, signal) => request(`/courriers/${id}/historique`, { signal }),

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

  recherche: (params = {}, signal) => request(`/recherche${buildQuery(params)}`, { signal }),

  utilisateurs: (params = {}) => request(`/users${buildQuery(params)}`),

  creerUtilisateur: (data) =>
    request("/users", { method: "POST", body: JSON.stringify(data) }),

  modifierUtilisateur: (id, data) =>
    request(`/users/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  resetMotDePasse: (id, mot_de_passe) =>
    request(`/users/${id}/reset-password`, {
      method: "POST",
      body: JSON.stringify({ mot_de_passe }),
    }),

  audit: (params = {}) => request(`/audit${buildQuery(params)}`),

  smtpStatus: () => request("/admin/smtp"),

  testSmtp: (email) =>
    request("/admin/smtp/test", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  listBackups: () => request("/admin/backups"),

  createBackup: () => request("/admin/backups", { method: "POST" }),

  restoreBackup: (nom_fichier, confirmation) =>
    request("/admin/backups/restore", {
      method: "POST",
      body: JSON.stringify({ nom_fichier, confirmation }),
    }),

  notificationCount: () => request("/notifications/unread-count"),

  notifications: (params = {}) => request(`/notifications${buildQuery(params)}`),

  markNotificationRead: (id) =>
    request(`/notifications/${id}/read`, { method: "PATCH" }),

  markAllNotificationsRead: () =>
    request("/notifications/read-all", { method: "POST" }),

  courriersAValider: (params = {}) =>
    request(`/courriers/a-valider${buildQuery(params)}`),

  migrationStatus: () => request("/admin/migration"),

  uploadMigrationDb: (file) => {
    const form = new FormData();
    form.append("fichier", file);
    return request("/admin/migration/upload", { method: "POST", body: form });
  },

  runMigration: (entite_defaut = "IBI", dry_run = false) =>
    request("/admin/migration/run", {
      method: "POST",
      body: JSON.stringify({ entite_defaut, dry_run }),
    }),

  ocrExtract: (file) => {
    const form = new FormData();
    form.append("fichier", file);
    return request("/ocr/extract", { method: "POST", body: form });
  },

  uploadSignature: (blob) => {
    const form = new FormData();
    form.append("fichier", blob, "signature.png");
    return request("/auth/signature", { method: "POST", body: form });
  },

  deleteSignature: () => request("/auth/signature", { method: "DELETE" }),

  signerCourrier: (id) => request(`/courriers/${id}/signer`, { method: "POST" }),
};

function downloadBlob(path, filename) {
  return fetch(`${API_BASE}${path}`, fetchOptions)
    .then((r) => {
      if (r.status === 401) {
        redirigerSessionExpiree();
        throw new Error("Session expirée");
      }
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
  return downloadBlob(`/pieces-jointes/${pieceId}/download`, nom);
}

export function downloadPdf(courrierId, numero) {
  return downloadBlob(`/courriers/${courrierId}/pdf`, `${numero}.pdf`);
}

export function exportRecherchePdf(filtres) {
  const qs = buildQuery(filtres);
  const date = new Date().toISOString().slice(0, 10);
  return downloadBlob(`/recherche/export-pdf${qs}`, `rapport_recherche_${date}.pdf`);
}

export function exportRechercheCsv(filtres) {
  const qs = buildQuery(filtres);
  const date = new Date().toISOString().slice(0, 10);
  return downloadBlob(`/recherche/export-csv${qs}`, `rapport_recherche_${date}.csv`);
}

export function previewPiece(pieceId) {
  const url = `${API_BASE}/pieces-jointes/${pieceId}/view`;
  return fetch(url, fetchOptions).then((r) => {
    if (!r.ok) throw new Error("Prévisualisation impossible");
    return r.blob();
  }).then((blob) => {
    const objectUrl = URL.createObjectURL(blob);
    window.open(objectUrl, "_blank", "noopener,noreferrer");
    setTimeout(() => URL.revokeObjectURL(objectUrl), 60000);
  });
}

function printBlob(blob, titre = "Document") {
  const objectUrl = URL.createObjectURL(blob);
  const frame = document.createElement("iframe");
  frame.style.position = "fixed";
  frame.style.right = "0";
  frame.style.bottom = "0";
  frame.style.width = "0";
  frame.style.height = "0";
  frame.style.border = "none";
  frame.src = objectUrl;
  document.body.appendChild(frame);
  frame.onload = () => {
    frame.contentWindow?.focus();
    frame.contentWindow?.print();
    setTimeout(() => {
      document.body.removeChild(frame);
      URL.revokeObjectURL(objectUrl);
    }, 60000);
  };
}

export function printPiece(pieceId) {
  return fetch(`${API_BASE}/pieces-jointes/${pieceId}/view`, fetchOptions)
    .then((r) => {
      if (!r.ok) throw new Error("Impression impossible");
      return r.blob();
    })
    .then((blob) => printBlob(blob));
}

export function printPdf(courrierId, numero) {
  return fetch(`${API_BASE}/courriers/${courrierId}/pdf`, fetchOptions)
    .then((r) => {
      if (!r.ok) throw new Error("Impression impossible");
      return r.blob();
    })
    .then((blob) => printBlob(blob, numero));
}

export function downloadBackup(nom) {
  return downloadBlob(`/admin/backups/${encodeURIComponent(nom)}/download`, nom);
}

export function downloadRapportMensuel(annee, mois) {
  const qs = buildQuery({ annee, mois });
  return downloadBlob(`/rapports/mensuel${qs}`, `rapport_mensuel_${annee}_${String(mois).padStart(2, "0")}.pdf`);
}
