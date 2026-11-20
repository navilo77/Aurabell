"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser, redirectByRole } from "@/lib/auth";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const user = getCurrentUser();
    if (user) {
      redirectByRole(user.roles);
    } else {
      router.push("/shop");
    }
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-foreground mb-4">Aura Bell</h1>
        <p className="text-muted-foreground">Loading marketplace...</p>
      </div>
    </div>
  );
}
