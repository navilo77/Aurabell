import { DecodedToken, TokenResponse, UserRole } from "@/lib/types";

const TOKEN_KEY = "aura_access_token";

export function setAccessToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return localStorage.getItem(TOKEN_KEY);
}

export function clearAccessToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function setTokenResponse(token: TokenResponse): void {
  setAccessToken(token.access_token);
  setRefreshToken(token.refresh_token);
}

export function setRefreshToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("aura_refresh_token", token);
  }
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return localStorage.getItem("aura_refresh_token");
}

export function clearAuth(): void {
  clearAccessToken();
  if (typeof window !== "undefined") {
    localStorage.removeItem("aura_refresh_token");
  }
}

export function decodeToken(token: string): DecodedToken | null {
  try {
    const payload = token.split(".")[1];
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload) as DecodedToken;
  } catch {
    return null;
  }
}

export function getUserRoles(): UserRole[] {
  const token = getAccessToken();
  if (!token) {
    return ["customer"];
  }
  const decoded = decodeToken(token);
  if (!decoded?.role) {
    const tokenAny = decoded as Record<string, unknown>;
    const roleClaim = tokenAny["role"];
    if (typeof roleClaim === "string") {
      return [roleClaim as UserRole];
    }
  }
  return ["customer"];
}

export function getCurrentUser() {
  const token = getAccessToken();
  if (!token) {
    return null;
  }
  const decoded = decodeToken(token);
  if (!decoded) {
    return null;
  }
  const roles: UserRole[] = [];
  const tokenAny = decoded as Record<string, unknown>;
  const roleClaim = tokenAny["role"];
  if (typeof roleClaim === "string") {
    roles.push(roleClaim as UserRole);
  }
  if (decoded.sub && decoded.email) {
    return { id: decoded.sub, email: decoded.email, roles };
  }
  return { id: decoded.sub ?? "", email: decoded.email ?? "", roles };
}

export function redirectByRole(roles: UserRole[]): void {
  const isOwnerAdmin =
    roles.includes("owner") || roles.includes("admin") || roles.includes("super_admin");
  const isStoreManager = roles.includes("store_manager");

  if (isStoreManager) {
    window.location.href = "/store-admin";
  } else if (isOwnerAdmin) {
    window.location.href = "/super-admin";
  } else {
    window.location.href = "/shop";
  }
}

export function getAuthHeaders(): Record<string, string> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}
