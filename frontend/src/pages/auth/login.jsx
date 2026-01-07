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

  const styles = {
    container:
      "min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 flex items-center justify-center px-4 relative",
    backgroundContainer:
      "fixed inset-0 overflow-hidden pointer-events-none z-0",
    backgroundBlob1:
      "absolute -top-40 -right-40 w-80 h-80 bg-green-400 rounded-full mix-blend-multiply blur-xl opacity-20 animate-blob",
    backgroundBlob2:
      "absolute -bottom-40 -left-40 w-80 h-80 bg-emerald-400 rounded-full mix-blend-multiply blur-xl opacity-20 animate-blob animation-delay-2000",
    backgroundBlob3:
      "absolute top-1/2 left-1/2 w-80 h-80 bg-teal-400 rounded-full mix-blend-multiply blur-xl opacity-20 animate-blob animation-delay-4000",
    contentWrapper:
      "relative z-10 w-full max-w-md mt-4",
    logoContainer:
      "inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-green-600 to-emerald-600 rounded-2xl shadow-lg mb-4",
    card:
      "bg-white rounded-2xl shadow-2xl p-8 border border-gray-100",
    title:
      "text-2xl font-bold text-gray-900 mb-1",
    subtitle:
      "text-sm text-gray-500",
    errorContainer:
      "mb-5 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg flex gap-3 animate-shake",
    inputContainer:
      "relative",
    inputIcon:
      "absolute inset-y-0 left-0 pl-4 mt-3 flex items-center pointer-events-none text-gray-400",
    input:
      "w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white focus:ring-2 focus:ring-green-500 focus:border-green-500 transition",
    inputError:
      "border-red-400 focus:ring-red-500 focus:border-red-500",
    inputPassword:
      "w-full pl-12 pr-12 py-3 border border-gray-300 rounded-lg bg-gray-50 focus:bg-white focus:ring-2 focus:ring-green-500 focus:border-green-500 transition",
    passwordToggle:
      "absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-green-600 transition",
    submitButton:
      "w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white py-3 rounded-lg font-semibold shadow-lg hover:shadow-xl hover:scale-[1.02] transition disabled:opacity-50 flex justify-center gap-2",
    link:
      "text-sm text-green-600 hover:text-green-800 font-medium",
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (loading) return;

    setError('');
    setLoading(true);

    try {
      const user = await login(credentials);
      navigate(getRouteByRole(user.role));
    } catch {
      setError("Nom d'utilisateur ou mot de passe incorrect.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      {/* Background */}
      <div className={styles.backgroundContainer}>
        <div className={styles.backgroundBlob1}></div>
        <div className={styles.backgroundBlob2}></div>
        <div className={styles.backgroundBlob3}></div>
      </div>

      <div className={styles.contentWrapper}>
        {/* Logo */}
        <div className="text-center mb-8">
          <div className={styles.logoContainer}>
            <i className="fas fa-robot text-white text-3xl"></i>
          </div>
          <h1 className="text-4xl font-bold text-gray-900">Agent AI</h1>
          <p className="text-gray-600">Connectez-vous à votre espace</p>
        </div>

        {/* Card */}
        <div className={styles.card}>
          <h2 className={styles.title}>Connexion</h2>
          <p className={`${styles.subtitle} mb-5`}>
            Entrez vos identifiants pour continuer
          </p>

          {/* Error */}
          {error && (
            <div className={styles.errorContainer}>
              <i className="fas fa-circle-exclamation text-red-500 mt-1"></i>
              <p className="text-sm text-red-800 flex-1">{error}</p>
              <button onClick={() => setError('')}>
                <i className="fas fa-xmark text-red-400 hover:text-red-600"></i>
              </button>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Nom d'utilisateur
              </label>
              <div className={styles.inputContainer}>
                <i className={`${styles.inputIcon} fas fa-user`}></i>
                <input
                  autoFocus
                  type="text"
                  required
                  disabled={loading}
                  value={credentials.username}
                  onChange={(e) =>
                    setCredentials({ ...credentials, username: e.target.value })
                  }
                  className={`${styles.input} ${
                    error ? styles.inputError : ''
                  }`}
                  placeholder="Votre nom d'utilisateur"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Mot de passe
              </label>
              <div className={styles.inputContainer}>
                <i className={`${styles.inputIcon} fas fa-lock`}></i>
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  disabled={loading}
                  value={credentials.password}
                  onChange={(e) =>
                    setCredentials({ ...credentials, password: e.target.value })
                  }
                  className={`${styles.inputPassword} ${
                    error ? styles.inputError : ''
                  }`}
                  placeholder="Votre mot de passe"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className={styles.passwordToggle}
                >
                  <i
                    className={`fas ${
                      showPassword
                        ? 'fa-eye-slash text-green-600'
                        : 'fa-eye'
                    }`}
                  ></i>
                </button>
              </div>
            </div>

            {/* Submit */}
            <button type="submit" disabled={loading} className={styles.submitButton}>
              {loading ? (
                <>
                  <i className="fas fa-spinner fa-spin"></i>
                  Connexion...
                </>
              ) : (
                <>
                  Se connecter
                  <i className="fas fa-arrow-right"></i>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p className="mt-6 text-center text-sm text-gray-500">
          © 2026 Perfeo Agent AI. Tous droits réservés.
        </p>
      </div>

      {/* Animations */}
      <style>{`
        @keyframes blob {
          0% { transform: translate(0) scale(1); }
          33% { transform: translate(30px,-50px) scale(1.1); }
          66% { transform: translate(-20px,20px) scale(0.9); }
          100% { transform: translate(0) scale(1); }
        }
        .animate-blob { animation: blob 7s infinite; }
        .animation-delay-2000 { animation-delay: 2s; }
        .animation-delay-4000 { animation-delay: 4s; }
        @keyframes shake {
          0%,100%{transform:translateX(0)}
          20%,60%{transform:translateX(-6px)}
          40%,80%{transform:translateX(6px)}
        }
        .animate-shake { animation: shake .4s }
      `}</style>
    </div>
  );
};

export default Login;
