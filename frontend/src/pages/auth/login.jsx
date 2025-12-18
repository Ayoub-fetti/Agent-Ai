import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { getRouteByRole } from '../../routes/roleRoutes';

const Login = () => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const user = await login(credentials);
      navigate(getRouteByRole(user.role));
    } catch{
      setError('Identifiants invalides');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded shadow-md w-96">
        <h2 className="text-2xl mb-6">Connexion</h2>
        {error && <div className="text-red-500 mb-4">{error}</div>}
        
        <input
          type="text"
          placeholder="Nom d'utilisateur"
          value={credentials.username}
          onChange={(e) => setCredentials({...credentials, username: e.target.value})}
          className="w-full p-3 border rounded mb-4"
          required
        />
        
        <input
          type="password"
          placeholder="Mot de passe"
          value={credentials.password}
          onChange={(e) => setCredentials({...credentials, password: e.target.value})}
          className="w-full p-3 border rounded mb-4"
          required
        />
        
        <button type="submit" className="w-full bg-blue-500 text-white p-3 rounded">
          Se connecter
        </button>
      </form>
    </div>
  );
};

export default Login;
