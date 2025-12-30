import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { getRouteByRole } from '../../routes/roleRoutes';

const Login = () => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  // Styles constants pour une meilleure organisation
  const styles = {
    container: "min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative",
    backgroundContainer: "fixed inset-0 overflow-hidden pointer-events-none z-0",
    backgroundBlob1: "absolute -top-40 -right-40 w-80 h-80 bg-green-400 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob",
    backgroundBlob2: "absolute -bottom-40 -left-40 w-80 h-80 bg-emerald-400 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000",
    backgroundBlob3: "absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-teal-400 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000",
    contentWrapper: "relative z-10 w-full max-w-md",
    logoContainer: "inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-green-600 to-emerald-600 rounded-2xl shadow-lg mb-4 transform hover:scale-105 transition-transform duration-200",
    card: "bg-white rounded-2xl shadow-2xl p-8 border border-gray-100",
    title: "text-2xl font-bold text-gray-900 mb-2",
    subtitle: "text-sm text-gray-500",
    errorContainer: "mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg flex items-start gap-3 animate-shake",
    inputContainer: "relative",
    inputIcon: "absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none",
    input: "w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200 bg-gray-50 focus:bg-white",
    inputPassword: "w-full pl-12 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200 bg-gray-50 focus:bg-white",
    passwordToggle: "absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-green-600 transition-colors",
    checkbox: "w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500 focus:ring-2",
    link: "text-sm text-green-600 hover:text-green-800 font-medium transition-colors",
    submitButton: "w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white py-3 px-4 rounded-lg font-semibold shadow-lg hover:shadow-xl hover:from-green-700 hover:to-emerald-700 transform hover:scale-[1.02] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:hover:from-green-600 disabled:hover:to-emerald-600 flex items-center justify-center gap-2",
    divider: "w-full border-t border-gray-300",
    dividerText: "px-4 bg-white text-gray-500"
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const user = await login(credentials);
      navigate(getRouteByRole(user.role));
    } catch (err) {
      setError('Identifiants invalides. Veuillez réessayer.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      {/* Background decoration avec couleurs vertes - Fixed pour rester en arrière-plan lors du scroll */}
      <div className={styles.backgroundContainer}>
        <div className={styles.backgroundBlob1}></div>
        <div className={styles.backgroundBlob2}></div>
        <div className={styles.backgroundBlob3}></div>
      </div>

      {/* Contenu principal avec z-index pour être au-dessus des blobs */}
      <div className={styles.contentWrapper}>
        {/* Logo/Brand Section */}
        <div className="text-center mb-8">
          <div className={styles.logoContainer}>
            <i className="fas fa-shield-alt text-white text-3xl"></i>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Agent AI</h1>
          <p className="text-gray-600">Connectez-vous à votre espace de travail</p>
        </div>

        {/* Login Card */}
        <div className={styles.card}>
          <div className="mb-6">
            <h2 className={styles.title}>Connexion</h2>
            <p className={styles.subtitle}>Entrez vos identifiants pour accéder</p>
          </div>

          {/* Error Message */}
          {error && (
            <div className={styles.errorContainer}>
              <i className="fas fa-exclamation-circle text-red-500 mt-0.5"></i>
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800">{error}</p>
              </div>
              <button
                onClick={() => setError('')}
                className="text-red-400 hover:text-red-600 transition-colors"
                aria-label="Fermer le message d'erreur"
              >
                <i className="fas fa-times"></i>
              </button>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username Field */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                <i className="fas fa-user mr-2 text-gray-400"></i>
                Nom d'utilisateur
              </label>
              <div className={styles.inputContainer}>
                <div className={styles.inputIcon}>
                  <i className="fas fa-user text-gray-400"></i>
                </div>
                <input
                  id="username"
                  type="text"
                  placeholder="Entrez votre nom d'utilisateur"
                  value={credentials.username}
                  onChange={(e) => setCredentials({...credentials, username: e.target.value})}
                  className={styles.input}
                  required
                  disabled={loading}
                  autoComplete="username"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                <i className="fas fa-lock mr-2 text-gray-400"></i>
                Mot de passe
              </label>
              <div className={styles.inputContainer}>
                <div className={styles.inputIcon}>
                  <i className="fas fa-lock text-gray-400"></i>
                </div>
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Entrez votre mot de passe"
                  value={credentials.password}
                  onChange={(e) => setCredentials({...credentials, password: e.target.value})}
                  className={styles.inputPassword}
                  required
                  disabled={loading}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className={styles.passwordToggle}
                  disabled={loading}
                  aria-label={showPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"}
                >
                  <i className={`fas ${showPassword ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                </button>
              </div>
            </div>

            {/* Remember Me & Forgot Password */}
            {/* <div className="flex items-center justify-between">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className={styles.checkbox}
                  disabled={loading}
                />
                <span className="ml-2 text-sm text-gray-600">Se souvenir de moi</span>
              </label>
              <a
                href="#"
                className={styles.link}
                onClick={(e) => {
                  e.preventDefault();
                  // TODO: Implémenter la fonctionnalité de mot de passe oublié
                }}
              >
                Mot de passe oublié ?
              </a>
            </div> */}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className={styles.submitButton}
            >
              {loading ? (
                <>
                  <i className="fas fa-spinner fa-spin"></i>
                  <span>Connexion en cours...</span>
                </>
              ) : (
                <>
                  <span>Se connecter</span>
                  <i className="fas fa-arrow-right"></i>
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="mt-6 mb-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className={styles.divider}></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className={styles.dividerText}>Ou</span>
              </div>
            </div>
          </div>

          {/* Additional Info */}
          <div className="text-center">
            <p className="text-sm text-gray-600">
              Besoin d'aide ?{' '}
              <a href="#" className={styles.link}>
                Contactez le support
              </a>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            © 2026 Perfeo Agent AI. Tous droits réservés.
          </p>
        </div>
      </div>

      {/* Custom animations */}
      <style>{`
        @keyframes blob {
          0% {
            transform: translate(0px, 0px) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
          100% {
            transform: translate(0px, 0px) scale(1);
          }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
          20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
        .animate-shake {
          animation: shake 0.5s;
        }
      `}</style>
    </div>
  );
};

export default Login;