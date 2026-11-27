"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { apiFetchOptional } from "@/lib/api";
import { UserProfileRead } from "@/lib/types";

interface AuthContextValue {
  user: UserProfileRead | null;
  isLoading: boolean;
  refetch: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<UserProfileRead | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUser = async () => {
    try {
      const data = await apiFetchOptional<UserProfileRead>("/users/me");
      setUser(data);
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();

    const handleAuthUpdated = () => {
      fetchUser();
    };

    window.addEventListener("auth-updated", handleAuthUpdated);
    return () => {
      window.removeEventListener("auth-updated", handleAuthUpdated);
    };
  }, []);

  const logout = async () => {
    try {
      await apiFetchOptional("/auth/logout", { method: "POST" });
    } catch {
      // Ignore error
    }
    setUser(null);
    window.dispatchEvent(new Event("auth-updated"));
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, refetch: fetchUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
}