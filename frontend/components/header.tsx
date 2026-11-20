"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import {
  ShoppingCart,
  User,
  Menu,
  X,
  Store,
  Search,
  Heart,
  LogOut,
  ChevronRight,
} from "lucide-react";
import { clearAccessToken, getAccessToken } from "@/lib/auth";

export function Header({ title }: { title?: string }) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    setIsLoggedIn(!!getAccessToken());
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleLogout = () => {
    clearAccessToken();
    window.location.href = "/login";
  };

  return (
    <>
      {/* প্রমোশনাল ব্যানার */}
      <div className="bg-gradient-to-r from-[hsl(262,83%,58%)] to-[hsl(290,70%,55%)] text-white text-center text-xs font-medium py-2 px-4">
        🎉 ফ্রি ডেলিভারি ঢাকায় ৫০০৳+ অর্ডারে &nbsp;•&nbsp; Free delivery in Dhaka on orders above ৳500
      </div>

      {/* মেইন হেডার */}
      <header
        className={`sticky top-0 z-50 transition-all duration-300 ${
          scrolled
            ? "bg-white/90 backdrop-blur-xl shadow-sm border-b border-border/50"
            : "bg-white border-b border-border"
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* বাম: মেনু + লোগো */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => setIsMenuOpen(true)}
                className="lg:hidden rounded-lg p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                aria-label="Open menu"
              >
                <Menu className="h-5 w-5" />
              </button>

              <Link href="/shop" className="flex items-center gap-2.5 group">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[hsl(262,83%,58%)] to-[hsl(290,70%,55%)] flex items-center justify-center shadow-md shadow-primary/25 group-hover:shadow-lg group-hover:shadow-primary/30 transition-shadow">
                  <Store className="h-5 w-5 text-white" />
                </div>
                <div className="hidden sm:block">
                  <span className="text-lg font-bold tracking-tight text-foreground">
                    Aura<span className="text-gradient"> Bell</span>
                  </span>
                </div>
              </Link>
            </div>

            {/* মধ্যে: সার্চ বার */}
            <div className="hidden md:flex flex-1 max-w-lg mx-8">
              <div className="relative w-full">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="পণ্য খুঁজুন... Search products"
                  className="w-full h-10 rounded-full border border-border bg-secondary/50 pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-all"
                />
              </div>
            </div>

            {/* ডানে: আইকন বাটনগুলো */}
            <div className="flex items-center gap-1">
              <button className="hidden sm:flex items-center justify-center w-10 h-10 rounded-full text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors" aria-label="Wishlist">
                <Heart className="h-5 w-5" />
              </button>

              <Link
                href="/shop/cart"
                className="relative flex items-center justify-center w-10 h-10 rounded-full text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                aria-label="Shopping cart"
              >
                <ShoppingCart className="h-5 w-5" />
                <span className="absolute -top-0.5 -right-0.5 inline-flex items-center justify-center min-w-[18px] h-[18px] rounded-full bg-gradient-to-r from-[hsl(262,83%,58%)] to-[hsl(290,70%,55%)] text-white text-[10px] font-bold px-1 shadow-sm">
                  0
                </span>
              </Link>

              {isLoggedIn ? (
                <div className="flex items-center gap-1 ml-1">
                  <Link
                    href="/profile"
                    className="flex items-center justify-center w-10 h-10 rounded-full text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                    aria-label="Profile"
                  >
                    <User className="h-5 w-5" />
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="hidden sm:flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-full border border-border bg-white text-foreground hover:bg-accent transition-colors"
                  >
                    <LogOut className="h-4 w-4" />
                    Sign out
                  </button>
                </div>
              ) : (
                <Link
                  href="/login"
                  className="ml-2 px-5 py-2 text-sm font-medium rounded-full bg-gradient-to-r from-[hsl(262,83%,58%)] to-[hsl(290,70%,55%)] text-white hover:opacity-90 shadow-md shadow-primary/25 hover:shadow-lg hover:shadow-primary/30 transition-all"
                >
                  Sign in
                </Link>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* মোবাইল মেনু ড্রয়ার */}
      {isMenuOpen && (
        <>
          <div
            className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
            onClick={() => setIsMenuOpen(false)}
          />
          <aside className="fixed inset-y-0 left-0 z-50 w-full max-w-[300px] bg-white shadow-2xl flex flex-col animate-in slide-in-from-left duration-300">
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[hsl(262,83%,58%)] to-[hsl(290,70%,55%)] flex items-center justify-center">
                  <Store className="h-4 w-4 text-white" />
                </div>
                <span className="font-bold text-foreground">Aura Bell</span>
              </div>
              <button
                onClick={() => setIsMenuOpen(false)}
                className="rounded-lg p-1.5 text-muted-foreground hover:bg-accent transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* সার্চ */}
            <div className="px-4 py-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="পণ্য খুঁজুন..."
                  className="w-full h-10 rounded-lg border border-border bg-secondary/50 pl-9 pr-4 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>
            </div>

            <nav className="flex-1 px-3 py-2 overflow-y-auto space-y-1">
              <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Marketplace
              </div>
              {[
                { href: "/shop", label: "🛍️ Shop" },
                { href: "/shop/cart", label: "🛒 Cart" },
              ].map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsMenuOpen(false)}
                  className="flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium text-foreground hover:bg-accent transition-colors"
                >
                  {item.label}
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </Link>
              ))}

              <div className="px-3 py-2 mt-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Account
              </div>
              <Link
                href="/login"
                onClick={() => setIsMenuOpen(false)}
                className="flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium text-foreground hover:bg-accent transition-colors"
              >
                🔑 Sign in
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </Link>
            </nav>
          </aside>
        </>
      )}
    </>
  );
}
