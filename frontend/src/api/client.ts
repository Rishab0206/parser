export interface ApiError extends Error {
  error_code?: string;
  status?: number;
  details?: Record<string, any>;
}

export interface ApiFetchOptions extends RequestInit {
  timeoutMs?: number;
}

export async function apiFetch<T>(endpoint: string, options: ApiFetchOptions = {}): Promise<T> {
  const { timeoutMs = 20000, ...fetchOptions } = options;
  const defaultHeaders: Record<string, string> = {};
  if (!(fetchOptions.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  // Attach auth bearer token if logged in
  const token = localStorage.getItem('auth_token');
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || '';
  const url = endpoint.startsWith('http') ? endpoint : `${apiBase}${endpoint}`;

  const controller = new AbortController();
  const timerId = window.setTimeout(() => controller.abort(), timeoutMs);

  let response: Response;
  try {
    response = await fetch(url, {
      ...fetchOptions,
      signal: fetchOptions.signal || controller.signal,
      headers: {
        ...defaultHeaders,
        ...fetchOptions.headers,
      },
    });
  } catch (err: any) {
    window.clearTimeout(timerId);
    if (err?.name === 'AbortError') {
      const timeoutErr = new Error(`Request timed out after ${Math.round(timeoutMs / 1000)}s. Please try again.`) as ApiError;
      timeoutErr.status = 408;
      timeoutErr.error_code = 'REQUEST_TIMEOUT';
      throw timeoutErr;
    }
    const netErr = new Error(err?.message || 'Network error: Unable to reach server.') as ApiError;
    netErr.status = 0;
    netErr.error_code = 'NETWORK_ERROR';
    throw netErr;
  } finally {
    window.clearTimeout(timerId);
  }

  if (!response.ok) {
    let errorDetail = `Server returned HTTP ${response.status}.`;
    let errorCode = `HTTP_${response.status}`;
    let details: Record<string, any> = {};

    try {
      const rawText = await response.text();
      if (rawText) {
        try {
          const errJson = JSON.parse(rawText);
          errorDetail = errJson.message || errJson.detail || errorDetail;
          errorCode = errJson.error_code || errorCode;
          details = errJson.details || {};
        } catch {
          // Non-JSON response (e.g. Render 502/504 HTML proxy error)
          if (response.status === 502 || response.status === 503 || response.status === 504) {
            errorDetail = `Server timeout or memory limit reached (HTTP ${response.status}). Please retry or check file size.`;
          } else {
            errorDetail = `HTTP ${response.status}: ${rawText.replace(/<[^>]+>/g, ' ').trim().slice(0, 180)}`;
          }
        }
      }
    } catch {
      // keep status-based error
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
