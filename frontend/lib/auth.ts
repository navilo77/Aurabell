import { UserRole } from "@/lib/types";

const TOKEN_KEY = "aura_access_token";

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

export function decodeToken(token: string): { sub?: string; email?: string; role?: string; exp?: number; [key: string]: unknown } | null {
  try {
    const payload = token.split(".")[1];
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload) as { sub?: string; email?: string; role?: string; exp?: number; [key: string]: unknown };
  } catch {
    return null;
  }
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
  const roleClaim = decoded.role;
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
