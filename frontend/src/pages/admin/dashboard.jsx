import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';
import {
  getDashboardStats,
  getUsers,
  createUser,
  updateUserRole,
  toggleUserStatus,
  resetUserPassword
} from '../../services/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const AdminDashboard = () => {
  const { logout, user } = useAuth();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    password: '',
    role: 'AGENT TECHNIQUE'
  });
  const [newPassword, setNewPassword] = useState('');
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsRes, usersRes] = await Promise.all([
        getDashboardStats(),
        getUsers()
      ]);
      setStats(statsRes.data);
      setUsers(usersRes.data);
    } catch {
      showNotification('Erreur lors du chargement des données', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    try {
      await createUser(newUser);
      showNotification('Utilisateur ajouté avec succès');
      setShowAddModal(false);
      setNewUser({ username: '', email: '', password: '', role: 'AGENT TECHNIQUE' });
      loadData();
    } catch {
      showNotification('Erreur lors de la création', 'error');
    }
  };

  const handleUpdateRole = async (userId, newRole) => {
    try {
      await updateUserRole(userId, { role: newRole });
      showNotification('Rôle mis à jour');
      loadData();
    } catch {
      showNotification('Erreur lors de la mise à jour', 'error');
    }
  };

  const handleToggleStatus = async (userId) => {
    try {
      await toggleUserStatus(userId);
      showNotification('Statut modifié');
      loadData();
    } catch {
      showNotification('Erreur lors de la modification', 'error');
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (!selectedUser || !newPassword) return;
    try {
      await resetUserPassword(selectedUser.id, newPassword);
      showNotification('Mot de passe réinitialisé');
      setShowPasswordModal(false);
      setSelectedUser(null);
      setNewPassword('');
    } catch {
      showNotification('Erreur lors de la réinitialisation', 'error');
    }
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom'
      }
    }
  };

  if (loading && !stats) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl text-gray-600">Chargement...</div>
      </div>
    );
  }

  // Chart data
  const usersByRoleData = {
    labels: ['Admin', 'Agent Technique', 'Agent Commercial'],
    datasets: [{
      label: 'Utilisateurs par rôle',
      data: stats ? [
        stats.users.by_role.ADMIN,
        stats.users.by_role['AGENT TECHNIQUE'],
        stats.users.by_role['AGENT COMMERCIAL']
      ] : [0, 0, 0],
      backgroundColor: ['#ef4444', '#3b82f6', '#10b981'],
      borderWidth: 0
    }]
  };

  const leadsByTemperatureData = {
    labels: ['Chaud', 'Tiède', 'Froid'],
    datasets: [{
      label: 'Leads par température',
      data: stats ? [
        stats.leads.by_temperature.chaud,
        stats.leads.by_temperature.tiede,
        stats.leads.by_temperature.froid
      ] : [0, 0, 0],
      backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6'],
      borderWidth: 0
    }]
  };

  const ticketsData = {
    labels: ['Traités', 'En attente'],
    datasets: [{
      label: 'Tickets',
      data: stats ? [stats.tickets.processed, stats.tickets.pending] : [0, 0],
      backgroundColor: ['#10b981', '#f59e0b'],
      borderWidth: 0
    }]
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 px-6 py-3 rounded-lg text-white z-50 ${
          notification.type === 'success' ? 'bg-green-500' : 'bg-red-500'
        }`}>
          {notification.message}
        </div>
      )}

      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">Dashboard Administrateur</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-600">Bienvenue, {user?.username}</span>
            <button
              onClick={logout}
              className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded transition"
            >
              Déconnexion
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow p-6">
            <div className="text-gray-500 text-sm">Total Utilisateurs</div>
            <div className="text-3xl font-bold text-gray-800">{stats?.users.total || 0}</div>
            <div className="text-green-500 text-sm mt-2">
              {stats?.users.active || 0} actifs
            </div>
          </div>
          <div className="bg-white rounded-xl shadow p-6">
            <div className="text-gray-500 text-sm">Total Leads</div>
            <div className="text-3xl font-bold text-gray-800">{stats?.leads.total || 0}</div>
            <div className="text-blue-500 text-sm mt-2">
              {stats?.leads.conversion_rate || 0}% conversion
            </div>
          </div>
          <div className="bg-white rounded-xl shadow p-6">
            <div className="text-gray-500 text-sm">Total Tickets</div>
            <div className="text-3xl font-bold text-gray-800">{stats?.tickets.total || 0}</div>
            <div className="text-yellow-500 text-sm mt-2">
              {stats?.tickets.pending || 0} en attente
            </div>
          </div>
          <div className="bg-white rounded-xl shadow p-6">
            <div className="text-gray-500 text-sm">Taux de conversion</div>
            <div className="text-3xl font-bold text-gray-800">
              {stats?.leads.conversion_rate || 0}%
            </div>
            <div className="text-gray-400 text-sm mt-2">
              {stats?.leads.converted || 0} leads convertis
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Utilisateurs par Rôle</h2>
            <div className="h-64">
              <Doughnut data={usersByRoleData} options={chartOptions} />
            </div>
          </div>
          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Leads par Température</h2>
            <div className="h-64">
              <Doughnut data={leadsByTemperatureData} options={chartOptions} />
            </div>
          </div>
          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Tickets</h2>
            <div className="h-64">
              <Doughnut data={ticketsData} options={chartOptions} />
            </div>
          </div>
        </div>

        {/* User Management Section */}
        <div className="bg-white rounded-xl shadow">
          <div className="p-6 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-xl font-semibold">Gestion des Utilisateurs</h2>
            <button
              onClick={() => setShowAddModal(true)}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded transition"
            >
              + Ajouter Utilisateur
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nom</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rôle</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Statut</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{u.username}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-500">{u.email}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <select
                        value={u.role}
                        onChange={(e) => handleUpdateRole(u.id, e.target.value)}
                        className="border rounded px-2 py-1 text-sm"
                      >
                        <option value="ADMIN">Administrateur</option>
                        <option value="AGENT TECHNIQUE">Agent Technique</option>
                        <option value="AGENT COMMERCIAL">Agent Commercial</option>
                      </select>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        u.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {u.is_active ? 'Actif' : 'Inactif'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleToggleStatus(u.id)}
                          className={`px-3 py-1 text-xs rounded transition ${
                            u.is_active 
                              ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                              : 'bg-green-100 text-green-800 hover:bg-green-200'
                          }`}
                        >
                          {u.is_active ? 'Désactiver' : 'Activer'}
                        </button>
                        <button
                          onClick={() => {
                            setSelectedUser(u);
                            setShowPasswordModal(true);
                          }}
                          className="bg-gray-100 text-gray-800 px-3 py-1 text-xs rounded hover:bg-gray-200 transition"
                        >
                          MDP
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold mb-4">Ajouter un Utilisateur</h2>
            <form onSubmit={handleAddUser}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Nom d'utilisateur</label>
                <input
                  type="text"
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Mot de passe</label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                  required
                  minLength="8"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Rôle</label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                  className="w-full border rounded px-3 py-2"
                >
                  <option value="AGENT TECHNIQUE">Agent Technique</option>
                  <option value="AGENT COMMERCIAL">Agent Commercial</option>
                  <option value="ADMIN">Administrateur</option>
                </select>
              </div>
              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded transition"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                >
                  Ajouter
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reset Password Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold mb-4">
              Réinitialiser le mot de passe
            </h2>
            <p className="text-gray-600 mb-4">
              Utilisateur: <strong>{selectedUser?.username}</strong>
            </p>
            <form onSubmit={handleResetPassword}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nouveau mot de passe
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full border rounded px-3 py-2"
                  required
                  minLength="8"
                />
              </div>
              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => {
                    setShowPasswordModal(false);
                    setSelectedUser(null);
                    setNewPassword('');
                  }}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded transition"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                >
                  Réinitialiser
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;

