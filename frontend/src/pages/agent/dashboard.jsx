import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const AgentDashboard = () => {
  const { logout } = useAuth();
  
  return (
    <div className="p-6">
      <h1 className="text-2xl mb-4">Dashboard Agent Technique</h1>
      <div className="mb-4 space-x-2">
        <Link to="/tickets" className="bg-blue-500 text-white px-4 py-2 rounded">
          Voir les Tickets
        </Link>
      </div>
      <button onClick={logout} className="bg-red-500 text-white px-4 py-2 rounded">
        Déconnexion
      </button>
    </div>
  );
};

export default AgentDashboard;
