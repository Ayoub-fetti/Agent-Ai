import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const getNavLinks = () => {
    switch (user?.role) {
      case 'ADMIN':
        return [
          {
            to: '/admin/dashboard',
            label: 'Dashboard Admin',
            icon: 'fa-solid fa-user-shield',
          },
        ];

      case 'AGENT TECHNIQUE':
        return [
          {
            to: '/agent/dashboard',
            label: 'Dashboard',
            icon: 'fa-solid fa-gauge',
          },
          {
            to: '/tickets',
            label: 'Tickets',
            icon: 'fa-solid fa-ticket',
          },
        ];

      case 'AGENT COMMERCIAL':
        return [
          {
            to: '/commercial/dashboard',
            label: 'Dashboard Commercial',
            icon: 'fa-solid fa-briefcase',
          },
        ];

      default:
        return [];
    }
  };

  return (
    <nav className="bg-white border-b shadow-sm">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex justify-between h-16">

          {/* Logo */}
          <div className="flex items-center space-x-10">
            <Link
              to="/"
              className="flex items-center space-x-2 text-green-600 font-bold text-lg"
            >
              <img
                src="/assets/images/logo-ai.png"
                alt='Agent Ai Logo'
                className='w-8 h-8 rounded-lg'
              />
            </Link>

            {/* Links */}
            <div className="hidden md:flex space-x-2">
              {getNavLinks().map((link) => {
                const isActive = location.pathname === link.to;

                return (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition
                      ${
                        isActive
                          ? 'bg-green-100 text-green-700'
                          : 'text-gray-600 hover:bg-gray-100 hover:text-green-600'
                      }
                    `}
                  >
                    <i className={`${link.icon} text-sm`}></i>
                    <span>{link.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Right side */}
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2 text-gray-700 text-sm">
              <i className="fa-solid fa-circle-user text-lg"></i>
              <span>{user?.username}</span>
              <span className="text-xs text-gray-400">
                ({user?.role})
              </span>
            </div>

            <button
              onClick={handleLogout}
              className="flex items-center space-x-2 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md text-sm transition"
            >
              <i className="fa-solid fa-right-from-bracket"></i>
              <span>Déconnexion</span>
            </button>
          </div>

        </div>
      </div>
    </nav>
  );
};

export default Navbar;
