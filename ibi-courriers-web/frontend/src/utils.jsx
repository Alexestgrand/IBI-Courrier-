const ROLE_SERVICE = {
  comptabilite: "Comptabilité",
  marche: "Service Marché",
  achat: "DAF",
};

export const LIBELLES_ROLE = {
  admin: "Administrateur",
  dg: "Direction générale",
  reception: "Réception",
  comptabilite: "Comptabilité",
  marche: "Service Marché",
  achat: "DAF",
};

export const FILTRES_STATUT = [
  { label: "Tous", value: "" },
  { label: "En attente", value: "en_attente" },
  { label: "Transmis", value: "transmis" },
  { label: "Validé", value: "valide" },
  { label: "Rejeté", value: "rejete" },
  { label: "Archivé", value: "archive" },
];

export const URGENCES = [
  { label: "Normal", value: "normal" },
  { label: "Urgent", value: "urgent" },
  { label: "Très urgent", value: "très urgent" },
];

export function servicePourRole(role) {
  return ROLE_SERVICE[role] || null;
}

export const LIBELLES_STATUT = {
  en_attente: "En attente",
  transmis: "Transmis",
  valide: "Validé",
  rejete: "Rejeté",
  archive: "Archivé",
};

const LIBELLES = LIBELLES_STATUT;

export function BadgeStatut({ statut }) {
  const cls = `badge badge-${statut?.replace(" ", "\\ ")}`;
  return <span className={cls}>{LIBELLES[statut] || statut}</span>;
}

export function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatTaille(octets) {
  if (octets < 1024) return `${octets} o`;
  if (octets < 1024 * 1024) return `${(octets / 1024).toFixed(1)} Ko`;
  return `${(octets / (1024 * 1024)).toFixed(1)} Mo`;
}
