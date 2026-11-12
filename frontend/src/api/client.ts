export interface ApiError extends Error {
  error_code?: string;
  details?: Record<string, any>;
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const defaultHeaders: Record<string, string> = {};
  if (!(options.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json';
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

    const err = new Error(errorDetail) as ApiError;
    err.error_code = errorCode;
    err.details = details;
    throw err;
  }

  return response.json();
}

