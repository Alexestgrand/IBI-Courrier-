const LIBELLES = {
  en_attente: "En attente",
  transmis: "Transmis",
  valide: "Validé",
  rejete: "Rejeté",
  archive: "Archivé",
};

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
