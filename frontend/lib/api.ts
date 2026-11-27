export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const isRefreshEndpoint = path === "/auth/refresh";

  const res = await fetchRaw(path, options);

  if (res.status === 401 && !isRefreshEndpoint) {
    const refreshed = await refreshSession();
    if (refreshed) {
      // Retry the original request once, preserving method/body/headers
      const retried = await fetchRaw(path, options);
      return parseResponse(retried);
    }
    // Refresh failed: end the auth lifecycle
    await handleAuthFailure();
    throw new Error("Session expired: refresh failed");
  }

  return parseResponse(res);
}

export async function apiFetchOptional<T>(path: string, options: RequestInit = {}): Promise<T | null> {
  const isRefreshEndpoint = path === "/auth/refresh";

  const res = await fetchRaw(path, options);

  if (res.status === 401 && !isRefreshEndpoint) {
    const refreshed = await refreshSession();
    if (refreshed) {
      const retried = await fetchRaw(path, options);
      return parseResponse(retried);
    }
    // Return null instead of triggering auth failure redirect
    return null;
  }

  if (!res.ok) {
    return null;
  }

  return parseResponse(res);
}

async function fetchRaw(path: string, options: RequestInit = {}): Promise<Response> {
  return fetch(`/api/v1${path}`, {
    ...options,
    credentials: "include",
    headers: {
      ...options.headers,
      ...(options.body ? { "Content-Type": "application/json" } : {}),
    },
  });
}

async function parseResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    const error = new Error(errorBody.detail || errorBody.message || `API error: ${res.status}`);
    (error as { status?: number }).status = res.status;
    throw error;
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

// ─── Refresh lifecycle ───

// Shared refresh promise so concurrent 401s coalesce into a single
// /auth/refresh request. Null when no refresh is in-flight.
let refreshPromise: Promise<void> | null = null;

async function refreshSession(): Promise<boolean> {
  // If a refresh is already in-flight, all callers wait on the same promise
  if (refreshPromise) {
    try {
      await refreshPromise;
      return true;
    } catch {
      return false;
    }
  }

  refreshPromise = (async () => {
    try {
      const res = await fetch("/api/v1/auth/refresh", {
        method: "POST",
        credentials: "include",
      });
      if (!res.ok) {
        throw new Error(`Refresh failed: ${res.status}`);
      }
    } finally {
      refreshPromise = null;
    }
  })();

  try {
    await refreshPromise;
    return true;
  } catch {
    return false;
  }
}

async function handleAuthFailure(): Promise<void> {
  // Best-effort server-side session clearing
  try {
    await fetch("/api/v1/auth/logout", {
      method: "POST",
      credentials: "include",
    });
  } catch {
    // Ignore - best effort
  }

  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}
