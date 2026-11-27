"use client";

import { useState } from "react";
import Link from "next/link";

interface LoginFormProps {
  onSubmit: (email: string, password: string) => void | Promise<void>;
  loading?: boolean;
  error?: string | null;
}

export function LoginForm({ onSubmit, loading, error }: LoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(email, password);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-md mx-auto">
      <h2 className="text-center text-2xl font-bold text-foreground">Welcome back</h2>
      <p className="text-center text-sm text-muted-foreground">
        Sign in to continue shopping on Aura Bell Marketplace
      </p>

      <div className="space-y-3">
        <label className="block text-sm font-medium text-foreground">Email</label>
        <input
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          placeholder="you@example.com"
          disabled={loading}
        />
        <label className="block text-sm font-medium text-foreground">Password</label>
        <input
          type="password"
          required
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          placeholder="••••••••"
          disabled={loading}
        />
      </div>

      {error && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-xs text-destructive">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full flex justify-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-70 transition-colors"
      >
        {loading ? "Signing in..." : "Sign in"}
      </button>

      <p className="text-center text-sm text-muted-foreground">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="font-medium text-primary hover:text-primary/80">
          Create account
        </Link>
      </p>
    </form>
  );
}
