import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import ProtectedRoute from "./ProtectedRoute";
import Layout from "../components/Layout";
import Login from "../pages/auth/login";
import AdminDashboard from "../pages/admin/dashboard";
import AgentDashboard from "../pages/agent/dashboard";
import CommercialDashboard from "../pages/commercial/dashboard";
import { getRouteByRole } from "./roleRoutes";
import TicketList from "../pages/agent/TicketList";
import TicketDetail from "../pages/agent/TicketDetail";

const AppRoutes = () => {
  const { user, loading } = useAuth();

  if (loading) return <div>Loading...</div>;

  return (
    <Layout>
      <Routes>
        <Route
          path="/login"
          element={
            user ? <Navigate to={getRouteByRole(user.role)} replace /> : <Login />
          }
        />

        <Route
          path="/tickets"
          element={
            <ProtectedRoute allowedRoles={["AGENT TECHNIQUE", "ADMIN"]}>
              <TicketList />
            </ProtectedRoute>
          }
        />
        <Route
          path="/tickets/:id"
          element={
            <ProtectedRoute allowedRoles={["AGENT TECHNIQUE", "ADMIN"]}>
              <TicketDetail />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/dashboard"
          element={
            <ProtectedRoute allowedRoles={["ADMIN"]}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/agent/dashboard"
          element={
            <ProtectedRoute allowedRoles={["AGENT TECHNIQUE", "ADMIN"]}>
              <AgentDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/commercial/dashboard"
          element={
            <ProtectedRoute allowedRoles={["AGENT COMMERCIAL", "ADMIN"]}>
              <CommercialDashboard />
            </ProtectedRoute>
          }
        />

        <Route path="/unauthorized" element={<div>Accès non autorisé</div>} />
        <Route 
          path="/" 
          element={
            user ? (
              <Navigate to={getRouteByRole(user.role)} replace />
            ) : (
              <Navigate to="/login" replace />
            )
          } 
        />
      </Routes>
    </Layout>
  );
};

export default AppRoutes;
