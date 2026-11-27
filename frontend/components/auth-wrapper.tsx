"use client";

import { AuthProvider } from "@/lib/auth-context";
import { ReactNode } from "react";

interface AuthWrapperProps {
  children: ReactNode;
}

export function AuthWrapper({ children }: AuthWrapperProps) {
  return <AuthProvider>{children}</AuthProvider>;
}