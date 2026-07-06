import { lazy, Suspense } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const CourriersEntrants = lazy(() => import("./pages/CourriersEntrants"));
const CourriersSortants = lazy(() => import("./pages/CourriersSortants"));
const NouveauCourrier = lazy(() => import("./pages/NouveauCourrier"));
const NouveauSortant = lazy(() => import("./pages/NouveauSortant"));
const CourrierDetail = lazy(() => import("./pages/CourrierDetail"));
const Recherche = lazy(() => import("./pages/Recherche"));
const Utilisateurs = lazy(() => import("./pages/Utilisateurs"));
const Sauvegardes = lazy(() => import("./pages/Sauvegardes"));
const Aide = lazy(() => import("./pages/Aide"));
const AValider = lazy(() => import("./pages/AValider"));
const Rapports = lazy(() => import("./pages/Rapports"));
const Profil = lazy(() => import("./pages/Profil"));

function PageLoader() {
  return (
    <p className="loading-text" style={{ padding: "2rem" }}>
      Chargement…
    </p>
  );
}

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <PageLoader />;
  if (!user) return <Navigate to="/login" replace />;

  if (user.must_change_password && location.pathname !== "/profil") {
    return <Navigate to="/profil" replace state={{ forcePassword: true }} />;
  }

  return children;
}

function AdminRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <PageLoader />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "admin") return <Navigate to="/" replace />;
  return children;
}

function DgRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <PageLoader />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "dg" && user.role !== "admin") {
    return <Navigate to="/" replace />;
  }
  return children;
}

export default function App() {
  return (
    <Suspense fallback={<PageLoader />}>
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
            path="dg/a-valider"
            element={
              <DgRoute>
                <AValider />
              </DgRoute>
            }
          />
          <Route
            path="rapports"
            element={
              <DgRoute>
                <Rapports />
              </DgRoute>
            }
          />
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
    </Suspense>
  );
}
