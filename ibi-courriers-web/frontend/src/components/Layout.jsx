import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import NotificationBell from "./NotificationBell";
import InstallPrompt from "./InstallPrompt";
import OfflineBanner from "./OfflineBanner";

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
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
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
  aide: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
  admin: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
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
  const isDg = user?.role === "dg" || isAdmin;

  const nav = [
    { to: "/", end: true, label: "Tableau de bord", icon: ICONS.dashboard },
    ...(isDg
      ? [{ to: "/dg/a-valider", label: "À valider", icon: ICONS.valider }]
      : []),
    { to: "/courriers/entrants", label: "Entrants", icon: ICONS.entrants },
    { to: "/courriers/sortants", label: "Sortants", icon: ICONS.sortants },
    { to: "/recherche", label: "Recherche", icon: ICONS.recherche },
    ...(isDg ? [{ to: "/rapports", label: "Rapports", icon: ICONS.rapports }] : []),
    ...(isAdmin
      ? [
          { to: "/admin/utilisateurs", label: "Utilisateurs", icon: ICONS.users },
          { to: "/admin/sauvegardes", label: "Administration", icon: ICONS.admin },
        ]
      : []),
    { to: "/aide", label: "Aide", icon: ICONS.aide },
    { to: "/profil", label: "Profil", icon: ICONS.profil },
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <img src="/logo-ibi.png" alt="IBI" className="sidebar__logo" />
          <div>
            <div className="sidebar__title">IBI Courriers</div>
            <div className="sidebar__subtitle">Groupe IBI</div>
          </div>
        </div>

        <nav className="sidebar__nav">
          {nav.map(({ to, end, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                isActive ? "sidebar__link active" : "sidebar__link"
              }
            >
              <span className="sidebar__icon-wrap">{icon}</span>
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar__footer">
          <button
            className="sidebar__link sidebar__logout"
            onClick={logout}
            type="button"
          >
            <span className="sidebar__icon-wrap">{ICONS.logout}</span>
            <span>Déconnexion</span>
          </button>
        </div>
      </aside>

      <div className="app-main">
        <OfflineBanner />
        <InstallPrompt />
        <header className="topbar">
          <NotificationBell />
          <div className="topbar__user">
            <div>
              <div className="topbar__name">
                {user?.prenom} {user?.nom}
              </div>
              <div className="topbar__role">{user?.role}</div>
            </div>
            <div className="topbar__avatar">{initiales || "?"}</div>
          </div>
        </header>
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
