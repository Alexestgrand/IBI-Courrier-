import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import BackgroundScene from "./components/BackgroundScene";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import CourriersEntrants from "./pages/CourriersEntrants";
import NouveauCourrier from "./pages/NouveauCourrier";
import CourrierDetail from "./pages/CourrierDetail";

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <p style={{ padding: "2rem" }}>Chargement…</p>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <>
      <BackgroundScene />
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
        <Route path="courriers/:id" element={<CourrierDetail />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
