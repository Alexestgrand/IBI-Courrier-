import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import CourriersEntrants from "./pages/CourriersEntrants";
import CourriersSortants from "./pages/CourriersSortants";
import NouveauCourrier from "./pages/NouveauCourrier";
import NouveauSortant from "./pages/NouveauSortant";
import CourrierDetail from "./pages/CourrierDetail";
import Recherche from "./pages/Recherche";
import Utilisateurs from "./pages/Utilisateurs";
import Sauvegardes from "./pages/Sauvegardes";
import Aide from "./pages/Aide";
import Profil from "./pages/Profil";

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <p className="loading-text" style={{ padding: "2rem" }}>
        Chargement…
      </p>
    );
  }
  if (!user) return <Navigate to="/login" replace />;

  if (user.must_change_password && location.pathname !== "/profil") {
    return <Navigate to="/profil" replace state={{ forcePassword: true }} />;
  }

  return children;
}

function AdminRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <p className="loading-text" style={{ padding: "2rem" }}>
        Chargement…
      </p>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "admin") return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="courriers/entrants" element={<CourriersEntrants />} />
          <Route path="courriers/nouveau" element={<NouveauCourrier />} />
          <Route path="courriers/sortants" element={<CourriersSortants />} />
          <Route path="courriers/sortant/nouveau" element={<NouveauSortant />} />
          <Route path="courriers/:id" element={<CourrierDetail />} />
          <Route path="recherche" element={<Recherche />} />
          <Route path="profil" element={<Profil />} />
          <Route path="aide" element={<Aide />} />
          <Route
            path="admin/utilisateurs"
            element={
              <AdminRoute>
                <Utilisateurs />
              </AdminRoute>
            }
          />
          <Route
            path="admin/sauvegardes"
            element={
              <AdminRoute>
                <Sauvegardes />
              </AdminRoute>
            }
          />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
