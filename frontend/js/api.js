/**
 * BLOODCARE - Centralized API Service
 * Supports GET, POST, PUT, DELETE with credentials for session cookies.
 */

const API_BASE = (function () {
  // If running from same origin (Flask served), use /api
  if (window.location.protocol.startsWith('http')) {
    return window.location.origin + '/api';
  }
  return 'http://127.0.0.1:5000/api';
})();

class ApiError extends Error {
  constructor(message, status = 500, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function request(path, options = {}) {
  const url = path.startsWith('http') ? path : `${API_BASE}${path.startsWith('/') ? path : '/' + path}`;
  
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...(options.headers || {})
  };

  const fetchOptions = {
    method: options.method || 'GET',
    headers,
    credentials: 'include', // Includes HTTP-only session cookie
    ...options
  };

  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    fetchOptions.body = JSON.stringify(options.body);
  }

  let response;
  try {
    response = await fetch(url, fetchOptions);
  } catch (err) {
    throw new ApiError(
      'Unable to connect to BLOODCARE server. Please ensure the backend is running at ' + API_BASE,
      0
    );
  }

  // Parse JSON response
  let json;
  try {
    json = await response.json();
  } catch (e) {
    json = null;
  }

  if (!response.ok) {
    const errorMsg = (json && (json.message || json.error)) || `Server returned HTTP ${response.status}`;
    
    // Automatic handling for 401 Unauthorized
    if (response.status === 401 && !options.silentAuth) {
      const isAuthPage = window.location.pathname.includes('login') || window.location.pathname.includes('register');
      if (!isAuthPage) {
        console.warn('Session expired or unauthorized. Redirecting to login...');
      }
    }
    
    throw new ApiError(errorMsg, response.status, json);
  }

  // Return standard payload: unwraps json.data if backend used standard success format
  return json;
}

const api = {
  base: API_BASE,
  get: (path, options) => request(path, { method: 'GET', ...options }),
  post: (path, body, options) => request(path, { method: 'POST', body, ...options }),
  put: (path, body, options) => request(path, { method: 'PUT', body, ...options }),
  del: (path, options) => request(path, { method: 'DELETE', ...options }),
};

window.api = api;
window.ApiError = ApiError;
