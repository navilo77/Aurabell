"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { hasAnyRole } from "@/lib/roles";
import { UserRole } from "@/lib/types";

export function RoleGuard({
  allowed,
  children,
}: {
  allowed: UserRole[];
  children: React.ReactNode;
}) {
  const [authorized, setAuthorized] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const user = await apiFetch<{ roles: UserRole[] }>("/users/me");
        if (mounted) {
          setAuthorized(hasAnyRole(user.roles, allowed));
        }
      } catch {
        if (mounted) {
          setAuthorized(false);
          window.location.href = "/login";
        }
      }
    })();
    return () => {
      mounted = false;
    };
  }, [allowed]);

  if (authorized === null) {
    return null;
  }

  if (!authorized) {
    return null;
  }

  return <>{children}</>;
}
