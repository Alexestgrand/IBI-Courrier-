import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ICONS = {
  dashboard: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
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
  nouveau: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 5v14M5 12h14" />
    </svg>
  ),
  recherche: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  ),
  users: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
    </svg>
  ),
  profil: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  ),
  logout: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  ),
};

export default function Layout() {
  const { user, logout } = useAuth();
  const initiales = `${user?.prenom?.[0] || ""}${user?.nom?.[0] || ""}`.toUpperCase();
  const isAdmin = user?.role === "admin";

  const nav = [
    { to: "/", end: true, label: "Tableau de bord", icon: ICONS.dashboard },
    { to: "/courriers/entrants", label: "Courriers entrants", icon: ICONS.entrants },
    { to: "/courriers/sortants", label: "Courriers sortants", icon: ICONS.sortants },
    { to: "/courriers/nouveau", label: "Nouveau entrant", icon: ICONS.nouveau },
    { to: "/recherche", label: "Recherche", icon: ICONS.recherche },
    ...(isAdmin
      ? [{ to: "/admin/utilisateurs", label: "Utilisateurs", icon: ICONS.users }]
      : []),
    { to: "/profil", label: "Mon profil", icon: ICONS.profil },
  ];

  return (
    <div className="app-layout">
      <aside className="sidebar-pill glass-panel">
        <div className="sidebar-pill__logo" title="IBI Courriers">
          <img src="/logo-ibi.png" alt="IBI" className="sidebar-pill__logo-img" />
        </div>
        <nav className="sidebar-pill__nav">
          {nav.map(({ to, end, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className="sidebar-pill__link"
              title={label}
            >
              <span className="sidebar-pill__icon">{icon}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-pill__footer">
          <div className="sidebar-pill__avatar" title={`${user?.prenom} ${user?.nom}`}>
            {initiales || "?"}
          </div>
          <button
            className="sidebar-pill__link sidebar-pill__logout"
            onClick={logout}
            title="Déconnexion"
            type="button"
          >
            <span className="sidebar-pill__icon">{ICONS.logout}</span>
          </button>
        </div>
      </aside>

      <div className="main-shell glass-panel">
        <header className="main-shell__header">
          <div>
            <p className="main-shell__eyebrow">Groupe IBI Côte d&apos;Ivoire</p>
            <h1 className="main-shell__brand">IBI Courriers</h1>
          </div>
          <div className="main-shell__user">
            <div>
              <strong>
                {user?.prenom} {user?.nom}
              </strong>
              <span>{user?.role}</span>
            </div>
            <div className="main-shell__avatar">{initiales || "?"}</div>
          </div>
        </header>
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
