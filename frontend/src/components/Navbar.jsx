import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const getNavLinks = () => {
    switch (user?.role) {
      case 'ADMIN':
        return [
          { to: '/admin/dashboard', label: 'Dashboard Admin' }
        ];
      case 'AGENT TECHNIQUE':
        return [
          { to: '/agent/dashboard', label: 'Dashboard' },
          { to: '/tickets', label: 'Tickets' }
        ];
      case 'AGENT COMMERCIAL':
        return [
          { to: '/commercial/dashboard', label: 'Dashboard Commercial' }
        ];
      default:
        return [];
    }
  };

  return (
    <nav className="bg-white shadow-lg border-b">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="text-xl font-bold text-green-600">
              Agent AI
            </Link>
            <div className="ml-10 flex space-x-8">
              {getNavLinks().map((link) => (
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
            <span className="text-sm text-gray-700">{user?.username}</span>
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

export default Navbar
