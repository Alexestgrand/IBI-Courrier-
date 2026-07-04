import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV = [
  {
    to: "/",
    end: true,
    label: "Tableau de bord",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </svg>
    ),
  },
  {
    to: "/courriers/entrants",
    label: "Courriers entrants",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
        <path d="M5.45 5.11L2 12v6a2 2 0 002 2h16a2 2 0 002-2v-6l-3.45-6.89A2 2 0 0016.76 4H7.24a2 2 0 00-1.79 1.11z" />
      </svg>
    ),
  },
  {
    to: "/courriers/nouveau",
    label: "Nouveau courrier",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 5v14M5 12h14" />
      </svg>
    ),
  },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const initiales = `${user?.prenom?.[0] || ""}${user?.nom?.[0] || ""}`.toUpperCase();

  return (
    <div className="app-layout">
      <aside className="sidebar-pill glass-panel">
        <div className="sidebar-pill__logo" title="IBI Courriers">
          I
        </div>
        <nav className="sidebar-pill__nav">
          {NAV.map(({ to, end, label, icon }) => (
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
            <span className="sidebar-pill__icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </span>
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
