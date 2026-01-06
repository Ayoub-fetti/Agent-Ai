import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const AdminNavbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const adminLinks = [
    { to: '/admin/dashboard', label: 'Admin Dashboard' },
    { to: '/agent/dashboard', label: 'Agent Dashboard' },
    { to: '/commercial/dashboard', label: 'Commercial Dashboard' },
    { to: '/tickets', label: 'Tickets' }
  ];

  return (
    <nav className="bg-white shadow-lg border-b">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="text-xl font-bold text-green-600">
              Agent AI - Admin
            </Link>
            <div className="ml-10 flex space-x-8">
              {adminLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className="text-gray-700 hover:text-green-600 px-3 py-2 text-sm font-medium"
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-700">{user?.username} (Admin)</span>
            <button
              onClick={handleLogout}
              className="bg-red-500 text-white px-4 py-2 rounded text-sm hover:bg-red-600"
            >
              Déconnexion
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default AdminNavbar;
