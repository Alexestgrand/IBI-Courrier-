import { Link, useLocation } from "react-router-dom";

const LABELS = {
  "/": "Tableau de bord",
  "/courriers/entrants": "Courriers entrants",
  "/courriers/nouveau": "Nouveau courrier entrant",
  "/courriers/sortants": "Courriers sortants",
  "/courriers/sortant/nouveau": "Nouveau courrier sortant",
  "/recherche": "Recherche",
  "/dg/a-valider": "À valider",
  "/rapports": "Rapports",
  "/admin/utilisateurs": "Utilisateurs",
  "/admin/sauvegardes": "Administration",
  "/aide": "Aide",
  "/profil": "Mon profil",
};

function filAriane(pathname, search) {
  const crumbs = [{ to: "/", label: "Accueil" }];

  if (pathname.startsWith("/courriers/") && pathname !== "/courriers/entrants" && pathname !== "/courriers/sortants" && pathname !== "/courriers/nouveau" && pathname !== "/courriers/sortant/nouveau") {
    crumbs.push({ to: "/courriers/entrants", label: "Courriers" });
    crumbs.push({ to: pathname, label: "Fiche courrier" });
    return crumbs;
  }

  const base = pathname + (search || "");
  const label = LABELS[pathname];
  if (label) {
    if (pathname === "/") return [{ to: "/", label: "Tableau de bord" }];
    crumbs.push({ to: base, label });
    if (search.includes("statut=en_attente")) crumbs[crumbs.length - 1].label = "Entrants — en attente";
    if (search.includes("urgents=1")) crumbs[crumbs.length - 1].label = "Entrants — urgents";
  }
  return crumbs;
}

export default function Breadcrumbs() {
  const { pathname, search } = useLocation();
  const crumbs = filAriane(pathname, search);
  if (crumbs.length <= 1 && pathname === "/") return null;

  return (
    <nav className="breadcrumbs" aria-label="Fil d'Ariane">
      {crumbs.map((crumb, i) => (
        <span key={crumb.to} className="breadcrumbs__item">
          {i > 0 && <span className="breadcrumbs__sep" aria-hidden="true">›</span>}
          {i === crumbs.length - 1 ? (
            <span className="breadcrumbs__current">{crumb.label}</span>
          ) : (
            <Link to={crumb.to}>{crumb.label}</Link>
          )}
        </span>
      ))}
    </nav>
  );
}
