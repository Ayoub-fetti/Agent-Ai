import { useAuth } from '../../contexts/AuthContext';

const AgentDashboard = () => {
  const { logout } = useAuth();
  
  return (
    <div className="p-6">
      <h1 className="text-2xl mb-4">Dashboard Agent Technique</h1>
      <button onClick={logout} className="bg-red-500 text-white px-4 py-2 rounded">
        Déconnexion
      </button>
    </div>
  );
};

export default AgentDashboard;
