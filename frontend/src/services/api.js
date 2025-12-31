import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor pour refresh automatique
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh');


      if (refreshToken) {
        try {
          const response = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken
          });
          
          localStorage.setItem('token', response.data.access);
          
          // Retry la requête originale
          error.config.headers.Authorization = `Bearer ${response.data.access}`;
          return axios.request(error.config);
        } catch {
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Admin Dashboard Stats
export const getDashboardStats = () => api.get('/admin/dashboard/stats/');

// User Management
export const getUsers = () => api.get('/admin/users/');
export const createUser = (data) => api.post('/admin/users/create/', data);
export const updateUserRole = (userId, data) => api.patch(`/admin/users/${userId}/role/`, data);
export const toggleUserStatus = (userId) => api.patch(`/admin/users/${userId}/toggle/`);
export const resetUserPassword = (userId, password) => api.post(`/admin/users/${userId}/reset-password/`, { password });

export default api;
