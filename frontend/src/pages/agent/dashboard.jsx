import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';

const AgentDashboard = () => {
  const { logout } = useAuth();
  
  const syncTickets = () => {
    api.post('/tickets/sync/')
       .then(res => alert(`${res.data.synced} tickets synchronisés`))
       .catch(err => alert('Erreur de synchronisation',err));
  };
  
  return (
    <div className="p-6">
      <h1 className="text-2xl mb-4">Dashboard Agent Technique</h1>
      <div className="mb-4 space-x-2">
        <button onClick={syncTickets} className="bg-green-500 text-white px-4 py-2 rounded">
          Synchroniser Tickets
        </button>
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
