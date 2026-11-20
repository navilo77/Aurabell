import { UserRole } from "@/lib/types";

export type Role = UserRole;

export const SHOP_ROLES: Role[] = ["customer"];

export const STORE_ADMIN_ROLES: Role[] = ["store_manager"];

export const SUPER_ADMIN_ROLES: Role[] = ["owner", "admin", "super_admin"];

export function hasAnyRole(
  userRoles: UserRole[] | undefined,
  allowed: UserRole[]
): boolean {
  if (!userRoles || userRoles.length === 0) {
    return false;
  }
  return userRoles.some((role) => allowed.includes(role));
}
