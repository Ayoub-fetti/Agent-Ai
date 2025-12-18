import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ProtectedRoute from './ProtectedRoute';
import Login from '../pages/auth/login';
import AdminDashboard from '../pages/admin/dashboard';
import AgentDashboard from '../pages/agent/dashboard';
import CommercialDashboard from '../pages/commercial/dashboard';
import { getRouteByRole } from './roleRoutes';

const AppRoutes = () => {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to={getRouteByRole(user.role)} replace /> : <Login />} />
      
      <Route path="/admin/dashboard" element={
        <ProtectedRoute allowedRoles={['ADMIN']}>
          <AdminDashboard />
        </ProtectedRoute>
      } />
      
      <Route path="/agent/dashboard" element={
        <ProtectedRoute allowedRoles={['AGENT TECHNIQUE']}>
          <AgentDashboard />
        </ProtectedRoute>
      } />
      
      <Route path="/commercial/dashboard" element={
        <ProtectedRoute allowedRoles={['AGENT COMMERCIAL']}>
          <CommercialDashboard />
        </ProtectedRoute>
      } />
      
      <Route path="/unauthorized" element={<div>Accès non autorisé</div>} />
      <Route path="/" element={<Navigate to="/login" replace />} />
    </Routes>
  );
};

export default AppRoutes;
