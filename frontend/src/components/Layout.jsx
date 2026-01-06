import { useAuth } from '../contexts/AuthContext';
import Navbar from './Navbar';
import AdminNavbar from './AdminNavbar';

const Layout = ({ children }) => {
  const { user } = useAuth();

  const renderNavbar = () => {
    if (user?.role === 'ADMIN') {
      return <AdminNavbar />;
    }
    return <Navbar />;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {user && renderNavbar()}
      <main className={user ? 'pt-4' : ''}>
        {children}
      </main>
    </div>
  );
};

export default Layout;
