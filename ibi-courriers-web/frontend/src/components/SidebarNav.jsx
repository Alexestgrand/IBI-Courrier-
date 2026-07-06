import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ICONS = {
  dashboard: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  ),
  entrants: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
      <path d="M5.45 5.11L2 12v6a2 2 0 002 2h16a2 2 0 002-2v-6l-3.45-6.89A2 2 0 0016.76 4H7.24a2 2 0 00-1.79 1.11z" />
    </svg>
  ),
  sortants: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  ),
  recherche: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  ),
  valider: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M9 11l3 3L22 4" />
      <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
    </svg>
  ),
  rapports: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  ),
  users: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
      <circle cx="9" cy="7" r="4" />
    </svg>
  ),
  admin: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42" />
    </svg>
  ),
  aide: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" />
    </svg>
  ),
  profil: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  ),
  chevron: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="6 9 12 15 18 9" />
    </svg>
  ),
};

function NavSection({ id, label, icon, items, defaultOpen = true }) {
  const location = useLocation();
  const actif = items.some(
    (item) =>
      location.pathname + location.search === item.to ||
      (item.to.split("?")[0] === location.pathname && !item.to.includes("?")),
  );
  const [open, setOpen] = useState(defaultOpen || actif);

  return (
    <div className={`sidebar-section ${open ? "is-open" : ""}`}>
      <button
        type="button"
        className="sidebar-section__toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="sidebar__icon-wrap">{icon}</span>
        <span className="sidebar-section__label">{label}</span>
        <span className="sidebar-section__chevron">{ICONS.chevron}</span>
      </button>
      {open && (
        <div className="sidebar-section__items">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => {
                const lienActif =
                  isActive ||
                  (item.to.includes("?") &&
                    `${location.pathname}${location.search}` === item.to);
                return `sidebar__sublink${item.cta ? " sidebar__sublink--cta" : ""}${lienActif ? " active" : ""}`;
              }}
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  );
}

export default function SidebarNav() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const isDg = user?.role === "dg" || isAdmin;
  const peutCreerEntrant = ["admin", "dg", "reception"].includes(user?.role);

  return (
    <nav className="sidebar__nav">
      <NavLink
        to="/"
        end
        className={({ isActive }) => (isActive ? "sidebar__link active" : "sidebar__link")}
      >
        <span className="sidebar__icon-wrap">{ICONS.dashboard}</span>
        <span>Tableau de bord</span>
      </NavLink>

      {peutCreerEntrant && (
        <NavLink to="/courriers/nouveau" className="sidebar__cta">
          + Nouveau courrier entrant
        </NavLink>
      )}

      <NavSection
        id="entrants"
        label="Courriers entrants"
        icon={ICONS.entrants}
        items={[
          { to: "/courriers/entrants", label: "Liste des entrants", end: true },
          ...(peutCreerEntrant
            ? [{ to: "/courriers/nouveau", label: "Nouveau courrier entrant", cta: true }]
            : []),
          { to: "/courriers/entrants?statut=en_attente", label: "En attente" },
          { to: "/courriers/entrants?urgents=1", label: "Urgents" },
        ]}
      />

      <NavSection
        id="sortants"
        label="Courriers sortants"
        icon={ICONS.sortants}
        items={[
          { to: "/courriers/sortants", label: "Liste des sortants", end: true },
          { to: "/courriers/sortant/nouveau", label: "Nouveau courrier sortant", cta: true },
        ]}
      />

      <NavLink
        to="/recherche"
        className={({ isActive }) => (isActive ? "sidebar__link active" : "sidebar__link")}
      >
        <span className="sidebar__icon-wrap">{ICONS.recherche}</span>
        <span>Recherche</span>
      </NavLink>

      {isDg && (
        <NavSection
          id="direction"
          label="Direction"
          icon={ICONS.valider}
          items={[
            { to: "/dg/a-valider", label: "À valider" },
            { to: "/rapports", label: "Rapports mensuels" },
          ]}
        />
      )}

      {isAdmin && (
        <NavSection
          id="admin"
          label="Administration"
          icon={ICONS.admin}
          defaultOpen={false}
          items={[
            { to: "/admin/utilisateurs", label: "Utilisateurs" },
            { to: "/admin/sauvegardes", label: "Sauvegardes & e-mail" },
          ]}
        />
      )}

      <div className="sidebar__spacer" />

      <NavLink
        to="/aide"
        className={({ isActive }) => (isActive ? "sidebar__link active" : "sidebar__link")}
      >
        <span className="sidebar__icon-wrap">{ICONS.aide}</span>
        <span>Aide</span>
      </NavLink>

      <NavLink
        to="/profil"
        className={({ isActive }) => (isActive ? "sidebar__link active" : "sidebar__link")}
      >
        <span className="sidebar__icon-wrap">{ICONS.profil}</span>
        <span>Mon profil</span>
      </NavLink>
    </nav>
  );
}
