"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { Home, Store, ShoppingCart, User, Users } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export function MobileBottomBar() {
  const pathname = usePathname();
  const { user, isLoading } = useAuth();
  const [cartCount, setCartCount] = useState<number>(0);

  useEffect(() => {
    const refreshCart = () => {
      apiFetch<{ items?: any[] }>("/cart")
        .then((data) => {
          if (data?.items) {
            setCartCount(
              data.items.reduce((acc, item) => acc + (item.quantity || 1), 0)
            );
          }
        })
        .catch(() => {});
    };

    refreshCart();
    window.addEventListener("cart-updated", refreshCart);
    return () => window.removeEventListener("cart-updated", refreshCart);
  }, [pathname]);

  const handleNavClick = (href: string, e: React.MouseEvent) => {
    if (href === "/shop/cart") {
      e.preventDefault();
      window.dispatchEvent(new Event("open-cart-drawer"));
    }
  };

  const isLoggedIn = !!user;

  const navItems = [
    {
      href: "/",
      label: "Home",
      icon: Home,
      active: pathname === "/",
    },
    {
      href: "/brand-shops",
      label: "Brand Shops",
      icon: Store,
      active: pathname.startsWith("/brand-shops") || pathname.startsWith("/shop"),
    },
    {
      href: "/community",
      label: "Community",
      icon: Users,
      active: pathname.startsWith("/community"),
    },
    {
      href: "/shop/cart",
      label: "Cart",
      icon: ShoppingCart,
      active: pathname.startsWith("/shop/cart"),
      badge: cartCount > 0 ? cartCount : undefined,
    },
    {
      href: isLoggedIn ? "/account" : "/login",
      label: isLoggedIn ? "Account" : "Sign In",
      icon: User,
      active:
        pathname.startsWith("/account") ||
        pathname.startsWith("/login") ||
        pathname.startsWith("/profile"),
    },
  ];

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#0c0e14]/95 backdrop-blur-2xl border-t border-gold-500/25 px-4 py-1.5 shadow-[0_-5px_25px_rgba(0,0,0,0.8)]"
      aria-label="Mobile Bottom Navigation"
    >
      <div className="flex items-center justify-around max-w-md mx-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={(e) => handleNavClick(item.href, e)}
              className={`relative min-w-[56px] min-h-[48px] flex flex-col items-center justify-center rounded-xl transition-all ${
                item.active
                  ? "text-gold-300 font-bold"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              <div className="relative">
                <Icon
                  className={`w-5 h-5 transition-transform ${
                    item.active ? "scale-110 text-gold-400" : ""
                  }`}
                />
                {item.badge !== undefined && (
                  <span className="absolute -top-1.5 -right-2.5 inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-black text-white bg-rose-600 rounded-full shadow-md">
                    {item.badge}
                  </span>
                )}
              </div>
              <span className="text-[10px] mt-1 tracking-tight">
                {item.label}
              </span>
              {item.active && (
                <span className="absolute bottom-0.5 w-6 h-0.5 rounded-full bg-gold-400 shadow-[0_0_8px_rgba(212,175,55,0.8)]" />
              )}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
