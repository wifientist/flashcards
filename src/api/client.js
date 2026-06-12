// Central API client.
//
// Wraps fetch with: credentialed requests by default, JSON helpers, and
// transparent access-token refresh. When a request gets a 401, we attempt a
// single POST /api/auth/refresh and replay the original request once. All
// concurrent 401s share one in-flight refresh so we never stampede the
// refresh endpoint. If refresh fails, we emit an "auth:logout" event so the
// AuthProvider can clear state, and throw ApiError.

export class ApiError extends Error {
  constructor(status, data) {
    super(data?.detail || `Request failed (${status})`);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

// Endpoints that must never trigger the refresh-and-retry loop.
const NO_REFRESH_PATHS = ['/api/auth/login', '/api/auth/refresh', '/api/auth/register'];

let refreshPromise = null;

function refreshAccessToken() {
  // Coalesce concurrent refreshes into a single network call.
  if (!refreshPromise) {
    refreshPromise = fetch('/api/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    })
      .then((res) => res.ok)
      .catch(() => false)
      .finally(() => {
        // Allow the next 401 (after this settles) to refresh again.
        setTimeout(() => {
          refreshPromise = null;
        }, 0);
      });
  }
  return refreshPromise;
}

async function parseBody(res) {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

/**
 * Make an API request. `path` should be the full path, e.g. "/api/cards".
 * Returns the parsed JSON body on success; throws ApiError on failure.
 */
export async function apiFetch(path, options = {}) {
  const opts = { credentials: 'include', ...options };

  let res = await fetch(path, opts);

  // Try a one-time refresh + replay on 401 (except for auth endpoints).
  if (res.status === 401 && !NO_REFRESH_PATHS.includes(path)) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      res = await fetch(path, opts);
    }
    if (res.status === 401) {
      window.dispatchEvent(new CustomEvent('auth:logout'));
    }
  }

  const body = await parseBody(res);
  if (!res.ok) {
    throw new ApiError(res.status, body);
  }
  return body;
}

/** Convenience helpers. */
export const api = {
  get: (path) => apiFetch(path),
  post: (path, json) =>
    apiFetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(json),
    }),
  put: (path, json) =>
    apiFetch(path, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(json),
    }),
  del: (path) => apiFetch(path, { method: 'DELETE' }),
};
