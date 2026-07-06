import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Breadcrumbs from "./Breadcrumbs";
import SidebarNav from "./SidebarNav";
import NotificationBell from "./NotificationBell";
import InstallPrompt from "./InstallPrompt";
import OfflineBanner from "./OfflineBanner";
import { LIBELLES_ROLE } from "../utils";

const ICONS = {
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
  const navigate = useNavigate();
  const initiales = `${user?.prenom?.[0] || ""}${user?.nom?.[0] || ""}`.toUpperCase();

  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">
        Aller au contenu
      </a>
      <aside className="sidebar">
        <div className="sidebar__brand">
          <img src="/logo-ibi.png" alt="IBI" className="sidebar__logo" />
          <div>
            <div className="sidebar__title">IBI Courriers</div>
            <div className="sidebar__subtitle">Groupe IBI</div>
          </div>
        </div>

        <SidebarNav />

        <div className="sidebar__footer">
          <button
            className="sidebar__link sidebar__logout"
            onClick={async () => {
              await logout();
              navigate("/login", { replace: true });
            }}
            type="button"
            aria-label="Déconnexion"
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
              <div className="topbar__role">
                {LIBELLES_ROLE[user?.role] || user?.role}
              </div>
            </div>
            <div className="topbar__avatar">{initiales || "?"}</div>
          </div>
        </header>
        <main id="main-content" className="page-content" tabIndex={-1}>
          <Breadcrumbs />
          <Outlet />
        </main>
      </div>
    </div>
  );
}
