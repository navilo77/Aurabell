"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import { UserRole } from "@/lib/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Mail, Lock, Phone, User, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

export default function RegisterPage() {
  const router = useRouter();
  const { refetch } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    password: "",
    confirmPassword: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    if (formData.password !== formData.confirmPassword) {
      setError("পাসওয়ার্ড মেলেনি");
      setLoading(false);
      return;
    }

    try {
      await apiFetch("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          full_name: formData.name,
          phone: formData.phone,
        }),
      });
      // Backend sets HttpOnly cookies only when a session was created.
      // Probe /users/me to determine whether the user is now authenticated.
      try {
        const user = await apiFetch<{
          id: string;
          email: string;
          roles: UserRole[];
          store_ids: string[];
        }>("/users/me");
        // Refresh auth context
        await refetch();
        // Redirect based on role
        if (user.roles.includes("super_admin")) {
          router.push("/super-admin");
        } else if (user.roles.includes("store_manager") || user.roles.includes("owner")) {
          router.push("/store-admin");
        } else {
          router.push("/");
        }
      } catch {
        // No session (email confirmation required) -> remain unauthenticated
        router.push("/login?registered=1");
      }
    } catch (err: any) {
      setError(err.message || "রেজিস্ট্রেশন করতে সমস্যা হচ্ছে");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">অ্যাকাউন্ট তৈরি করুন</CardTitle>
          <CardDescription>
            Aura Bell-এ আপনার অ্যাকাউন্টের জন্য নিবন্ধন করুন
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {error && (
            <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <label className="text-sm font-medium text-foreground sr-only">পূর্ণ নাম</label>
                </div>
                <Input
                  placeholder="আপনার পূর্ণ নাম"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <label className="text-sm font-medium text-foreground sr-only">ফোন নম্বর</label>
                </div>
                <Input
                  placeholder="ফোন নম্বর"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <label className="text-sm font-medium text-foreground sr-only">ইমেইল ঠিকানা</label>
              </div>
              <Input
                type="email"
                placeholder="name@example.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-muted-foreground" />
                <label className="text-sm font-medium text-foreground sr-only">পাসওয়ার্ড</label>
              </div>
              <Input
                type="password"
                placeholder="পাসওয়ার্ড (সর্বনিম্ন ৬ অক্ষর)"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-muted-foreground" />
                <label className="text-sm font-medium text-foreground sr-only">পাসওয়ার্ড নিশ্চিত করুন</label>
              </div>
              <Input
                type="password"
                placeholder="পাসওয়ার্ড আবার লিখুন"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              />
            </div>
            <Button type="submit" className="w-full h-11 bg-gradient-to-r from-[hsl(262,83%,58%)] to-[hsl(290,70%,55%)] text-white font-semibold shadow-lg shadow-primary/25 hover:shadow-lg hover:shadow-primary/40 transition-all" disabled={loading}>
              {loading ? (
                <ArrowRight className="h-5 w-5 animate-spin" />
              ) : (
                <>
                  অ্যাকাউন্ট তৈরি করুন <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </form>
        </CardContent>
        <CardContent className="border-t pt-6 text-center">
          <p className="text-sm text-muted-foreground">
            ইতিমধ্যে অ্যাকাউন্ট আছে?
            <Link
              href="/login"
              className="text-primary font-medium hover:text-primary/80 transition-colors"
            >
                লগইন করুন
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
