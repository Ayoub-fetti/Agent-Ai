export const ROLE_ROUTES = {
  'ADMIN': '/admin/dashboard',
  'AGENT TECHNIQUE': '/agent/dashboard', 
  'AGENT COMMERCIAL': '/commercial/dashboard'
};

export const getRouteByRole = (role) => ROLE_ROUTES[role] || '/';
