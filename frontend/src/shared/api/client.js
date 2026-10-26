/**
 * FoodVerse AI — Shared API client.
 *
 * Provides a unified fetch wrapper with configurable base URL,
 * automatic anonymous session header propagation (X-Session-ID),
 * timeout handling, and structured error normalization.
 */

export const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const SESSION_STORAGE_KEY = 'foodverse_session_id';
const AUTH_TOKEN_KEY = 'foodverse_auth_token';
const AUTH_USER_KEY = 'foodverse_auth_user';

export class ApiError extends Error {
  constructor(message, code = 'UNKNOWN_ERROR', status = 500, requestId = null, details = null) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.requestId = requestId;
    this.details = details;
  }
}

/**
 * Retrieve the current session token from localStorage if available.
 */
export function getSessionToken() {
  try {
    return localStorage.getItem(SESSION_STORAGE_KEY) || null;
  } catch {
    return null;
  }
}

/**
 * Retrieve the authenticated user token from localStorage.
 */
export function getAuthToken() {
  try {
    return localStorage.getItem(AUTH_TOKEN_KEY) || null;
  } catch {
    return null;
  }
}

/**
 * Store authenticated user session.
 */
export function setAuthSession(token, user) {
  try {
    if (token) localStorage.setItem(AUTH_TOKEN_KEY, token);
    if (user) localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
  } catch {
    // Ignore storage errors
  }
}

/**
 * Clear authenticated user session.
 */
export function clearAuthSession() {
  try {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
  } catch {
    // Ignore storage errors
  }
}

/**
 * Get cached user object.
 */
export function getStoredUser() {
  try {
    const raw = localStorage.getItem(AUTH_USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

/**
 * Capture and persist new session token from response headers.
 */
function captureSessionToken(response) {
  try {
    const token = response.headers.get('X-Session-ID');
    if (token) {
      localStorage.setItem(SESSION_STORAGE_KEY, token);
    }
  } catch {
    // LocalStorage may be unavailable in private modes; ignore
  }
}

/**
 * Build request headers including anonymous session token and auth bearer token.
 */
function buildHeaders(customHeaders = {}) {
  const headers = { ...customHeaders };
  const token = getSessionToken();
  if (token) {
    headers['X-Session-ID'] = token;
  }
  const authToken = getAuthToken();
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  return headers;
}

/**
 * Perform a multipart form-data POST request.
 *
 * @param {string} endpoint - API route (e.g. '/api/v1/food-analysis')
 * @param {FormData} formData - Payload
 * @param {object} [options] - Additional options (e.g. signal for abort)
 * @returns {Promise<any>}
 */
export async function postFormData(endpoint, formData, options = {}) {
  const url = `${BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: buildHeaders(options.headers || {}),
      body: formData,
      credentials: 'include',
      signal: options.signal,
    });

    captureSessionToken(response);

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorObj = data?.detail?.error || data?.error || {};
      const message =
        errorObj.message ||
        data?.detail ||
        `Request failed with status ${response.status}`;
      const code = errorObj.code || `HTTP_${response.status}`;
      const requestId = errorObj.request_id || null;

      throw new ApiError(message, code, response.status, requestId, data);
    }

    return data;
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    if (err.name === 'AbortError') {
      throw new ApiError('Analysis request was canceled.', 'REQUEST_ABORTED', 0);
    }
    throw new ApiError(
      err.message || 'Unable to connect to the FoodVerse AI backend server.',
      'NETWORK_ERROR',
      0
    );
  }
}

/**
 * Perform a JSON GET request.
 */
export async function getJson(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: buildHeaders({
        Accept: 'application/json',
        ...(options.headers || {}),
      }),
      credentials: 'include',
      signal: options.signal,
    });

    captureSessionToken(response);

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorObj = data?.detail?.error || data?.error || {};
      const message = errorObj.message || `Request failed with status ${response.status}`;
      throw new ApiError(message, errorObj.code || `HTTP_${response.status}`, response.status);
    }

    return data;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err.message || 'Unable to connect to service.', 'NETWORK_ERROR', 0);
  }
}

export { getJson as fetchJson };

/**
 * Perform a JSON POST request.
 */
export async function postJson(endpoint, body, options = {}) {
  const url = `${BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: buildHeaders({
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...(options.headers || {}),
      }),
      body: JSON.stringify(body),
      credentials: 'include',
      signal: options.signal,
    });

    captureSessionToken(response);

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorObj = data?.detail?.error || data?.error || {};
      const message = errorObj.message || `Request failed with status ${response.status}`;
      throw new ApiError(message, errorObj.code || `HTTP_${response.status}`, response.status);
    }

    return data;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err.message || 'Unable to connect to service.', 'NETWORK_ERROR', 0);
  }
}

/**
 * Perform a JSON DELETE request.
 */
export async function deleteJson(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      method: 'DELETE',
      headers: buildHeaders({
        Accept: 'application/json',
        ...(options.headers || {}),
      }),
      credentials: 'include',
      signal: options.signal,
    });

    captureSessionToken(response);

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorObj = data?.detail?.error || data?.error || {};
      const message = errorObj.message || `Delete failed with status ${response.status}`;
      throw new ApiError(message, errorObj.code || `HTTP_${response.status}`, response.status);
    }

    return data;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err.message || 'Unable to connect to service.', 'NETWORK_ERROR', 0);
  }
}
