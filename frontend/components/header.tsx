"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect, Suspense } from "react";
import {
  Home,
  Store,
  ShoppingCart,
  User,
  Search,
  Menu,
  X,
  LogOut,
  ChevronDown,
  Globe,
  Loader2,
  Users,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { LiveSearch } from "@/components/live-search";

export function Header({
  activeTab = "home",
  onSearch,
}: {
  title?: string;
  activeTab?: "home" | "stores" | "cart" | "account" | "community";
  onSearch?: (q: string) => void;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [cartCount, setCartCount] = useState<number>(0);
  const [lang, setLang] = useState<"BN" | "EN">("BN");
  const [searchQuery, setSearchQuery] = useState("");
  const { user, isLoading, logout } = useAuth();
  const isLoggedIn = !isLoading && !!user;

  useEffect(() => {
    const refreshCart = () => {
      apiFetch<{ items?: any[] }>("/cart")
        .then((data) => {
          if (data?.items) {
            setCartCount(data.items.reduce((acc, item) => acc + (item.quantity || 1), 0));
          }
        })
        .catch(() => {});
    };

    refreshCart();
    window.addEventListener("cart-updated", refreshCart);

    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => {
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("cart-updated", refreshCart);
    };
  }, []);

  const openCartDrawer = (e: React.MouseEvent) => {
    e.preventDefault();
    window.dispatchEvent(new Event("open-cart-drawer"));
  };

  const handleLogout = async () => {
    await logout();
    window.location.href = "/login";
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSearch) {
      onSearch(searchQuery);
    } else if (searchQuery.trim()) {
      router.push(`/shop?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const currentTab =
    pathname === "/"
      ? "home"
      : pathname.startsWith("/shop/cart")
      ? "cart"
      : pathname.startsWith("/brand-shops")
      ? "stores"
      : pathname.startsWith("/shop")
      ? "stores"
      : pathname.startsWith("/community")
      ? "community"
      : pathname.startsWith("/account") || pathname.startsWith("/profile")
      ? "account"
      : activeTab;

  return (
    <>
      <header
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 px-4 sm:px-6 lg:px-8 py-3 ${
          scrolled
            ? "bg-[#090b0e]/90 backdrop-blur-xl border-b border-gold-500/20 shadow-2xl shadow-black/80"
            : "bg-gradient-to-b from-black/80 via-black/40 to-transparent"
        }`}
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          {/* বাম পাশে: গোল্ডেন লাক্সারি লোগো */}
          <Link href="/" className="flex items-center gap-3 group flex-shrink-0">
            {/* গোল্ডেন ক্রাফটেড মনোগ্রাম "A" */}
            <div className="relative w-10 h-10 flex items-center justify-center">
              <div className="absolute inset-0 rounded-full border border-gold-400/30 group-hover:border-gold-400/60 transition-colors animate-pulse-gold" />
              <svg
                viewBox="0 0 100 100"
                className="w-8 h-8 text-gold-400 filter drop-shadow-[0_0_8px_rgba(212,175,55,0.7)]"
                fill="currentColor"
              >
                <path d="M50 12 L78 84 L64 84 L58 68 L42 68 L36 84 L22 84 Z M46 54 L54 54 L50 40 Z" />
                <path
                  d="M50 4 L54 16 L50 22 L46 16 Z"
                  fill="#ffe89e"
                />
              </svg>
            </div>

            <div className="flex flex-col">
              <span className="font-serif text-xl sm:text-2xl font-bold tracking-wider text-gold-gradient uppercase drop-shadow-sm">
                AURA BELL
              </span>
              <span className="text-[10px] sm:text-xs text-[#d1b87a] tracking-[0.22em] uppercase font-medium -mt-1">
                Shop Beyond Limits
              </span>
            </div>
          </Link>

          {/* মাঝখানে: ফ্লোটিং গ্লাস মরফিজম পিল ন্যাভিগেশন */}
          <nav className="hidden md:flex items-center gap-1.5 p-1.5 rounded-full bg-[#12161f]/80 backdrop-blur-xl border border-white/10 shadow-2xl">
            {/* Home */}
            <Link
              href="/"
              className={`flex items-center gap-2 px-5 py-2 rounded-full text-xs font-semibold tracking-wide transition-all duration-300 ${
                currentTab === "home"
                  ? "glass-pill-active text-[#ffe89e]"
                  : "text-zinc-300 hover:text-white hover:bg-white/5"
              }`}
            >
              <Home className="w-4 h-4 text-gold-400" />
              <span>Home</span>
            </Link>

            {/* Brand Shops */}
            <Link
              href="/brand-shops"
              className={`flex items-center gap-2 px-5 py-2 rounded-full text-xs font-semibold tracking-wide transition-all duration-300 ${
                currentTab === "stores"
                  ? "glass-pill-active text-[#ffe89e]"
                  : "text-zinc-300 hover:text-white hover:bg-white/5"
              }`}
            >
              <Store className="w-4 h-4 text-gold-400" />
              <span>Brand Shops</span>
            </Link>

            {/* Community */}
            <Link
              href="/community"
              className={`flex items-center gap-2 px-5 py-2 rounded-full text-xs font-semibold tracking-wide transition-all duration-300 ${
                pathname.startsWith("/community")
                  ? "glass-pill-active text-[#ffe89e]"
                  : "text-zinc-300 hover:text-white hover:bg-white/5"
              }`}
            >
              <Users className="w-4 h-4 text-gold-400" />
              <span>Community</span>
            </Link>

            {/* Cart */}
            <Link
              href="/shop/cart"
              onClick={openCartDrawer}
              className={`relative flex items-center gap-2 px-5 py-2 rounded-full text-xs font-semibold tracking-wide transition-all duration-300 ${
                currentTab === "cart"
                  ? "glass-pill-active text-[#ffe89e]"
                  : "text-zinc-300 hover:text-white hover:bg-white/5"
              }`}
            >
              <ShoppingCart className="w-4 h-4 text-gold-400" />
              <span>Cart</span>
              {cartCount > 0 && (
                <span className="inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-extrabold text-white bg-rose-600 rounded-full shadow-sm ml-0.5">
                  {cartCount}
                </span>
              )}
            </Link>

            {/* Account */}
            <Link
              href={isLoggedIn ? "/account" : "/login"}
              className={`flex items-center gap-2 px-5 py-2 rounded-full text-xs font-semibold tracking-wide transition-all duration-300 ${
                currentTab === "account"
                  ? "glass-pill-active text-[#ffe89e]"
                  : "text-zinc-300 hover:text-white hover:bg-white/5"
              }`}
            >
              <User className="w-4 h-4 text-gold-400" />
              <span>Account</span>
            </Link>
          </nav>

          {/* ডান পাশে: সার্চ বার + ভাষা + মোবাইল মেনু টগল */}
          <div className="flex items-center gap-2.5">
            {/* Live Search */}
            <div className="hidden sm:block">
              <Suspense fallback={<Loader2 className="h-8 w-8 animate-spin text-gold-400" />}>
                <LiveSearch />
              </Suspense>
            </div>

            {/* ভাষা ড্রপডাউন (BN / EN) */}
            <button
              onClick={() => setLang(lang === "BN" ? "EN" : "BN")}
              className="flex items-center gap-1.5 h-9 px-3 rounded-full bg-[#12161f]/80 backdrop-blur-md border border-white/10 text-xs font-semibold text-zinc-200 hover:border-gold-400/40 hover:text-gold-300 transition-colors"
              title="Change Language"
            >
              <Globe className="w-3.5 h-3.5 text-gold-400" />
              <span>{lang}</span>
              <ChevronDown className="w-3 h-3 text-zinc-400" />
            </button>

            {/* লগআউট বাটন (যদি লগইন থাকে) */}
            {isLoggedIn && (
              <button
                onClick={handleLogout}
                className="hidden lg:flex items-center gap-1.5 h-9 px-3 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-300 hover:bg-rose-500/20 text-xs font-medium transition-colors"
                title="Sign out"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Exit</span>
              </button>
            )}

            {/* মোবাইল মেনু বাটন */}
            <button
              onClick={() => setIsMenuOpen(true)}
              className="md:hidden flex items-center justify-center w-9 h-9 rounded-full bg-[#12161f]/80 border border-white/10 text-gold-400 hover:bg-white/5"
              aria-label="Open navigation menu"
            >
              <Menu className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* মোবাইল স্লাইড-আউট নেভিগেশন ড্রয়ার */}
      {isMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="fixed inset-0 bg-black/80 backdrop-blur-md"
            onClick={() => setIsMenuOpen(false)}
          />
          <aside className="fixed inset-y-0 left-0 w-4/5 max-w-xs bg-[#0c0e14] border-r border-gold-500/30 p-6 flex flex-col justify-between shadow-2xl animate-in slide-in-from-left duration-300">
            <div>
              {/* মোবাইল ড্রয়ার হেডার */}
              <div className="flex items-center justify-between pb-6 border-b border-white/10">
                <div className="flex items-center gap-2">
                  <span className="font-serif text-lg font-bold text-gold-gradient uppercase">
                    Aura Bell
                  </span>
                </div>
                <button
                  onClick={() => setIsMenuOpen(false)}
                  className="p-1 rounded-full text-zinc-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Mobile Live Search */}
              <div className="mt-4">
                <Suspense fallback={<Loader2 className="h-8 w-8 animate-spin text-gold-400" />}>
                  <LiveSearch />
                </Suspense>
              </div>

              {/* মোবাইল মেনু আইটেম */}
              <nav className="mt-6 space-y-2">
                <Link
                  href="/"
                  onClick={() => setIsMenuOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                    currentTab === "home"
                      ? "bg-gold-500/20 text-[#ffe89e] border border-gold-500/40"
                      : "text-zinc-300 hover:bg-white/5"
                  }`}
                >
                  <Home className="w-4 h-4 text-gold-400" />
                  <span>Home</span>
                </Link>

                <Link
                  href="/brand-shops"
                  onClick={() => setIsMenuOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                    currentTab === "stores"
                      ? "bg-gold-500/20 text-[#ffe89e] border border-gold-500/40"
                      : "text-zinc-300 hover:bg-white/5"
                  }`}
                >
                  <Store className="w-4 h-4 text-gold-400" />
                  <span>Brand Shops</span>
                </Link>

                <Link
                  href="/community"
                  onClick={() => setIsMenuOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                    pathname.startsWith("/community")
                      ? "bg-gold-500/20 text-gold-300 border border-gold-500/40"
                      : "text-zinc-300 hover:bg-white/5"
                  }`}
                >
                  <Users className="w-4 h-4 text-gold-400" />
                  <span>Community</span>
                </Link>

                <Link
                  href="/shop/cart"
                  onClick={() => setIsMenuOpen(false)}
                  className={`flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                    currentTab === "cart"
                      ? "bg-gold-500/20 text-[#ffe89e] border border-gold-500/40"
                      : "text-zinc-300 hover:bg-white/5"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <ShoppingCart className="w-4 h-4 text-gold-400" />
                    <span>Cart</span>
                  </div>
                  {cartCount > 0 && (
                    <span className="px-2 py-0.5 text-xs font-bold bg-rose-600 text-white rounded-full">
                      {cartCount}
                    </span>
                  )}
                </Link>

                <Link
                  href={isLoggedIn ? "/account" : "/login"}
                  onClick={() => setIsMenuOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                    currentTab === "account"
                      ? "bg-gold-500/20 text-[#ffe89e] border border-gold-500/40"
                      : "text-zinc-300 hover:bg-white/5"
                  }`}
                >
                  <User className="w-4 h-4 text-gold-400" />
                  <span>{isLoggedIn ? "Account Orders" : "Sign In"}</span>
                </Link>
              </nav>
            </div>

            {/* ড্রয়ার ফুটার */}
            <div className="pt-6 border-t border-white/10">
              {isLoggedIn ? (
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-rose-600/20 border border-rose-500/40 text-rose-300 text-sm font-semibold"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              ) : (
                <Link
                  href="/login"
                  onClick={() => setIsMenuOpen(false)}
                  className="w-full flex items-center justify-center py-2.5 rounded-xl bg-gold-gradient text-black font-semibold text-sm shadow-gold"
                >
                  Sign In to Aura Bell
                </Link>
              )}
            </div>
          </aside>
        </div>
      )}
    </>
  );
}
