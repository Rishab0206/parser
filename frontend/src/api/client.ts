export interface ApiError extends Error {
  error_code?: string;
  status?: number;
  details?: Record<string, any>;
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const defaultHeaders: Record<string, string> = {};
  if (!(options.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  // Attach auth bearer token if logged in
  const token = localStorage.getItem('auth_token');
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || '';
  const url = endpoint.startsWith('http') ? endpoint : `${apiBase}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    let errorDetail = "An error occurred while communicating with the server.";
    let errorCode = "HTTP_ERROR";
    let details: Record<string, any> = {};

    try {
      const errJson = await response.json();
      errorDetail = errJson.message || errJson.detail || errorDetail;
      errorCode = errJson.error_code || "REQUEST_FAILED";
      details = errJson.details || {};
    } catch {
      // keep default error
    }

    if (response.status === 401) {
      if (!endpoint.includes('/api/auth/login') && !endpoint.includes('/api/auth/invite') && !endpoint.includes('/api/auth/accept-invite')) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        window.location.href = '/login';
      }
    }

    if (response.status === 403) {
      errorCode = "FORBIDDEN";
      errorDetail = errorDetail || "Access Denied (403): You do not have permission to access this customer record.";
    }

    const err = new Error(errorDetail) as ApiError;
    err.status = response.status;
    err.error_code = errorCode;
    err.details = details;
    throw err;
  }

  return response.json();
}
