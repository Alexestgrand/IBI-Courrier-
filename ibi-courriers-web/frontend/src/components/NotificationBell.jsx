import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { formatDate } from "../utils";

export default function NotificationBell() {
  const [count, setCount] = useState(0);
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const panelRef = useRef(null);

  const refreshCount = () => {
    api.notificationCount().then((d) => setCount(d.count)).catch(() => {});
  };

  const loadItems = () => {
    setLoading(true);
    api
      .notifications({ limit: 20 })
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refreshCount();
    const interval = setInterval(refreshCount, 45000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!open) return;
    loadItems();
    const onClick = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  const marquerLue = async (id) => {
    try {
      await api.markNotificationRead(id);
      setItems((prev) =>
        prev.map((n) => (n.id === id ? { ...n, lu: true } : n))
      );
      setCount((c) => Math.max(0, c - 1));
    } catch {
      /* ignore */
    }
  };

  const toutLire = async () => {
    try {
      await api.markAllNotificationsRead();
      setItems((prev) => prev.map((n) => ({ ...n, lu: true })));
      setCount(0);
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="notif-bell" ref={panelRef}>
      <button
        type="button"
        className="notif-bell__btn"
        aria-label="Notifications"
        onClick={() => setOpen((v) => !v)}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 01-3.46 0" />
        </svg>
        {count > 0 && (
          <span className="notif-bell__badge">{count > 99 ? "99+" : count}</span>
        )}
      </button>

      {open && (
        <div className="notif-panel">
          <div className="notif-panel__header">
            <span>Notifications</span>
            {count > 0 && (
              <button type="button" className="btn-link" onClick={toutLire}>
                Tout marquer lu
              </button>
            )}
          </div>
          {loading ? (
            <p className="notif-panel__empty">Chargement…</p>
          ) : items.length === 0 ? (
            <p className="notif-panel__empty">Aucune notification.</p>
          ) : (
            <ul className="notif-list">
              {items.map((n) => (
                <li
                  key={n.id}
                  className={n.lu ? "notif-item notif-item--lu" : "notif-item"}
                >
                  <div className="notif-item__titre">{n.titre}</div>
                  <div className="notif-item__msg">{n.message}</div>
                  <div className="notif-item__footer">
                    <span>{formatDate(n.created_at)}</span>
                    <span className="notif-item__actions">
                      {n.courrier_id && (
                        <Link
                          to={`/courriers/${n.courrier_id}`}
                          onClick={() => {
                            if (!n.lu) marquerLue(n.id);
                            setOpen(false);
                          }}
                        >
                          Voir
                        </Link>
                      )}
                      {!n.lu && (
                        <button type="button" onClick={() => marquerLue(n.id)}>
                          Lu
                        </button>
                      )}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
