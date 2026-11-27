"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Header } from "@/components/header";
import { Hero2D } from "@/components/hero-2d";
import { ProductGrid } from "@/components/product-grid";
import { MobileBottomBar } from "@/components/mobile-bottom-bar";
import { ProductRead, StoreRead } from "@/lib/types";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { Shield, Sparkles, ExternalLink, Store, Flower2, Cpu, ChevronRight } from "lucide-react";

interface PriceCalculationRead {
  selling_price: number;
  final_price: number;
}

export default function HomePage() {
  const [products, setProducts] = useState<ProductRead[]>([]);
  const [stores, setStores] = useState<StoreRead[]>([]);
  const [selectedStoreId, setSelectedStoreId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prices, setPrices] = useState<Record<string, number>>({});
  const [adminRole, setAdminRole] = useState<string | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    let mounted = true;

    // Check if user is admin
    if (user?.roles) {
      if (user.roles.includes("super_admin")) setAdminRole("/super-admin");
      else if (user.roles.includes("store_manager") || user.roles.includes("owner"))
        setAdminRole("/store-admin");
    }

    Promise.all([
      apiFetch<ProductRead[]>("/products"),
      apiFetch<StoreRead[]>("/stores"),
    ])
      .then(async ([productsData, storesData]) => {
        if (!mounted) return;
        setProducts(productsData ?? []);
        setStores(storesData ?? []);

        // Calculate prices for the primary variant
        const priceMap: Record<string, number> = {};
        for (const p of productsData ?? []) {
          if (p.variants && p.variants.length > 0) {
            try {
              const priceData = await apiFetch<PriceCalculationRead>(
                `/pricing/calculate?variant_id=${p.variants[0].id}&store_id=${p.store_id}`
              );
              const rawPrice = priceData.final_price ?? priceData.selling_price;
              priceMap[p.id] =
                typeof rawPrice === "number" ? rawPrice : Number(rawPrice) || 0;
            } catch {
              priceMap[p.id] = 0;
            }
          }
        }
        if (mounted) setPrices(priceMap);
      })
      .catch((err) => {
        if (mounted) setError(err.message);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [user]);

  const productsWithPrice = products.map((p) => ({
    ...p,
    price: prices[p.id],
    compareAtPrice: undefined,
  }));

  const featuredProducts = productsWithPrice.slice(0, 8);

  const bestGadgetStore = stores.find((s) => s.slug === "best-gadget");
  const auraSkinCareStore = stores.find((s) => s.slug === "aura-skin-care");

  return (
    <div className="min-h-screen bg-[#090b0e] text-[#f7f6f0] selection:bg-gold-500/30 selection:text-gold-200 pb-20 md:pb-0">
      {/* Floating Glass Header */}
      <Header activeTab="home" />

      {/* Admin Dashboard Pill if user has staff role */}
      {adminRole && (
        <div className="fixed top-16 right-6 z-40">
          <Link
            href={adminRole}
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-gold-gradient text-black text-xs font-bold shadow-gold hover:scale-105 transition-transform"
          >
            <Shield className="w-3.5 h-3.5" />
            <span>Admin Dashboard</span>
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>
      )}

      {/* Aura Bell Platform Hero */}
      <section className="relative w-full overflow-hidden">
        <div className="relative w-full h-[60vh] min-h-[480px] max-h-[640px] flex items-center justify-center">
          <div
            className="absolute inset-0 bg-gradient-to-br from-[#0a1525] via-[#090b0e] to-[#1a0d16] pointer-events-none"
          />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(212,175,55,0.08)_0%,_transparent_70%)] pointer-events-none" />
          <div className="absolute inset-0 hero-vignette pointer-events-none" />

          <div className="relative z-10 text-center max-w-5xl mx-auto px-4 pt-16 flex flex-col items-center">
            {/* Platform Seal */}
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-black/60 backdrop-blur-xl border border-gold-400/40 text-gold-300 text-xs font-bold mb-4 shadow-gold">
              <Sparkles className="w-3.5 h-3.5 text-gold-400" />
              <span>Official Dual-Flagship Marketplace Platform</span>
            </div>

            {/* Grand Brand Logo */}
            <h1 className="font-serif text-4xl sm:text-6xl md:text-7xl font-black tracking-wider text-white drop-shadow-[0_4px_16px_rgba(0,0,0,0.9)]">
              AURA <span className="text-gold-gradient">BELL</span>
            </h1>
            <p className="font-serif text-xs sm:text-sm text-[#f5df88] tracking-[0.3em] uppercase font-bold mt-2 drop-shadow-md">
              Shop Beyond Limits
            </p>

            <p className="mt-4 text-xs sm:text-sm text-zinc-200 max-w-2xl mx-auto leading-relaxed drop-shadow-md">
              Experience authentic smart technology and luxury skincare from our two official flagship boutiques —
              unified in a single shared cart with seamless checkout.
            </p>

            {/* Store Portals - Platform Level */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-3xl mt-10">
              {/* Best Gadget Portal */}
              <Link
                href="/best-gadget"
                className={`group p-4 sm:p-5 rounded-2xl cursor-pointer transition-all duration-300 backdrop-blur-xl flex items-center justify-between border ${
                  bestGadgetStore
                    ? "bg-[#0c1a2e]/90 border-cyan-400 shadow-[0_0_25px_rgba(34,211,238,0.4)] scale-102"
                    : "bg-[#0a121c]/80 border-cyan-500/30 hover:border-cyan-400 hover:bg-[#0c1a2e]/90 hover:shadow-[0_0_20px_rgba(34,211,238,0.25)]"
                }`}
              >
                <div className="flex items-center gap-3.5 text-left">
                  <div className="w-11 h-11 rounded-xl bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300 group-hover:scale-110 transition-transform">
                    <Cpu className="w-5 h-5 text-cyan-400" />
                  </div>
                  <div>
                    <h3 className="font-serif text-sm sm:text-base font-bold text-white group-hover:text-cyan-300 transition-colors">
                      Best Gadget
                    </h3>
                    <p className="text-[11px] text-cyan-400 font-mono">
                      Smart Tech. Better Life.
                    </p>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-cyan-400 group-hover:translate-x-1 transition-transform" />
              </Link>

              {/* Aura Skin Care Portal */}
              <Link
                href="/aura-skin-care"
                className={`group p-4 sm:p-5 rounded-2xl cursor-pointer transition-all duration-300 backdrop-blur-xl flex items-center justify-between border ${
                  auraSkinCareStore
                    ? "bg-[#25101a]/90 border-rose-400 shadow-[0_0_25px_rgba(251,113,133,0.4)] scale-102"
                    : "bg-[#180a11]/80 border-rose-500/30 hover:border-rose-400 hover:bg-[#25101a]/90 hover:shadow-[0_0_20px_rgba(251,113,133,0.25)]"
                }`}
              >
                <div className="flex items-center gap-3.5 text-left">
                  <div className="w-11 h-11 rounded-xl bg-rose-500/20 border border-rose-400/40 flex items-center justify-center text-rose-300 group-hover:scale-110 transition-transform">
                    <Flower2 className="w-5 h-5 text-rose-300" />
                  </div>
                  <div>
                    <h3 className="font-serif text-sm sm:text-base font-bold text-white group-hover:text-rose-300 transition-colors">
                      Aura Skin Care
                    </h3>
                    <p className="text-[11px] text-rose-400 font-mono">
                      Glow Naturally.
                    </p>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-rose-400 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>

            {/* Explore All Button */}
            <Link
              href="/shop"
              className="mt-8 inline-flex items-center gap-2 px-6 py-2.5 rounded-full bg-gold-gradient text-black font-extrabold text-xs uppercase tracking-wider shadow-gold hover:opacity-95 transition-all group"
            >
              <span>Explore All Boutiques</span>
              <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>

        {/* Trust Guarantee Strip */}
        <div className="bg-[#0a0c11] border-y border-gold-500/10 py-2.5 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-center sm:justify-between gap-2 sm:gap-0">
            <div className="flex items-center gap-2 justify-center">
              <Shield className="w-4 h-4 text-gold-400 flex-shrink-0" />
              <p className="text-[11px] font-semibold text-zinc-300">100% Genuine Guarantee</p>
            </div>
            <div className="hidden sm:block w-px h-4 bg-white/10" />
            <div className="flex items-center gap-2 justify-center">
              <Store className="w-4 h-4 text-gold-400 flex-shrink-0" />
              <p className="text-[11px] font-semibold text-zinc-300">Shared Multi-Store Cart</p>
            </div>
            <div className="hidden sm:block w-px h-4 bg-white/10" />
            <div className="flex items-center gap-2 justify-center">
              <svg className="w-4 h-4 text-emerald-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6 0a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a6 6 0 016 0m6 0a2 2 0 10-4 0m-4 0a6 6 0 01-6 0" />
              </svg>
              <p className="text-[11px] font-semibold text-zinc-300">Cash on Delivery (COD)</p>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Products Section */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-gold-500/15 border border-gold-400/30 text-gold-300 text-xs font-semibold mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Curated Selections</span>
          </div>
          <h2 className="font-serif text-2xl sm:text-3xl font-extrabold text-white">
            Featured Across Both Flagships
          </h2>
          <p className="mt-1 text-xs sm:text-sm text-zinc-400">
            Hand-picked from Best Gadget and Aura Skin Care — add to a single shared cart.
          </p>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-10 h-10 rounded-full border-2 border-gold-400/20 border-t-gold-400 animate-spin mb-3" />
            <p className="text-xs text-gold-300 font-mono tracking-widest uppercase">
              Loading Products...
            </p>
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-6 text-center max-w-lg mx-auto">
            <p className="text-xs text-rose-300">{error}</p>
          </div>
        ) : (
          <ProductGrid
            products={featuredProducts as ProductRead[]}
            stores={stores}
            selectedStoreId={selectedStoreId}
            onStoreSelect={setSelectedStoreId}
          />
        )}
      </section>

      {/* Category Discovery */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12 border-t border-gold-500/10">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-gold-500/15 border border-gold-400/30 text-gold-300 text-xs font-semibold mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Browse by Category</span>
          </div>
          <h2 className="font-serif text-2xl sm:text-3xl font-extrabold text-white">
            Discover Collections
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Best Gadget Categories */}
          {bestGadgetStore && (
            <Link
              href="/best-gadget"
              className="group relative rounded-2xl overflow-hidden border border-cyan-500/30 bg-gradient-to-br from-[#0c1a2e] to-[#0a121c] p-6 shadow-xl hover:border-cyan-400 hover:shadow-[0_0_25px_rgba(34,211,238,0.3)] transition-all"
            >
              <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500/10 to-transparent pointer-events-none group-hover:from-cyan-500/20 transition-all" />
              <div className="relative z-10 flex flex-col">
                <div className="w-12 h-12 rounded-xl bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300 mb-3">
                  <Cpu className="w-6 h-6" />
                </div>
                <h3 className="font-serif text-lg font-bold text-white">Best Gadget</h3>
                <p className="text-xs text-cyan-300 mt-1">Smartphones, Laptops, Audio & Accessories</p>
                <div className="mt-auto flex items-center gap-1 text-cyan-400 text-xs font-mono">
                  <span>Explore</span>
                  <ChevronRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </Link>
          )}

          <Link
            href="/best-gadget"
            className="group relative rounded-2xl overflow-hidden border border-cyan-500/30 bg-gradient-to-br from-[#0c1a2e] to-[#0a121c] p-6 shadow-xl hover:border-cyan-400 hover:shadow-[0_0_25px_rgba(34,211,238,0.3)] transition-all"
          >
            <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500/10 to-transparent pointer-events-none group-hover:from-cyan-500/20 transition-all" />
            <div className="relative z-10 flex flex-col">
              <div className="w-12 h-12 rounded-xl bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300 mb-3">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                </svg>
              </div>
              <h3 className="font-serif text-lg font-bold text-white">All Tech</h3>
              <p className="text-xs text-cyan-300 mt-1">Browse all technology categories</p>
              <div className="mt-auto flex items-center gap-1 text-cyan-400 text-xs font-mono">
                <span>Browse</span>
                <ChevronRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </Link>

          {/* Aura Skin Care Categories */}
          {auraSkinCareStore && (
            <Link
              href="/aura-skin-care"
              className="group relative rounded-2xl overflow-hidden border border-rose-500/30 bg-gradient-to-br from-[#25101a] to-[#180a11] p-6 shadow-xl hover:border-rose-400 hover:shadow-[0_0_25px_rgba(251,113,133,0.3)] transition-all"
            >
              <div className="absolute inset-0 bg-gradient-to-tr from-rose-500/10 to-transparent pointer-events-none group-hover:from-rose-500/20 transition-all" />
              <div className="relative z-10 flex flex-col">
                <div className="w-12 h-12 rounded-xl bg-rose-500/20 border border-rose-400/40 flex items-center justify-center text-rose-300 mb-3">
                  <Flower2 className="w-6 h-6" />
                </div>
                <h3 className="font-serif text-lg font-bold text-white">Aura Skin Care</h3>
                <p className="text-xs text-rose-300 mt-1">Serums, Creams, Cleansers & Treatments</p>
                <div className="mt-auto flex items-center gap-1 text-rose-400 text-xs font-mono">
                  <span>Explore</span>
                  <ChevronRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </Link>
          )}

          <Link
            href="/aura-skin-care"
            className="group relative rounded-2xl overflow-hidden border border-rose-500/30 bg-gradient-to-br from-[#25101a] to-[#180a11] p-6 shadow-xl hover:border-rose-400 hover:shadow-[0_0_25px_rgba(251,113,133,0.3)] transition-all"
          >
            <div className="absolute inset-0 bg-gradient-to-tr from-rose-500/10 to-transparent pointer-events-none group-hover:from-rose-500/20 transition-all" />
            <div className="relative z-10 flex flex-col">
              <div className="w-12 h-12 rounded-xl bg-rose-500/20 border border-rose-400/40 flex items-center justify-center text-rose-300 mb-3">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 11c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                </svg>
              </div>
              <h3 className="font-serif text-lg font-bold text-white">All Beauty</h3>
              <p className="text-xs text-rose-300 mt-1">Browse all skincare categories</p>
              <div className="mt-auto flex items-center gap-1 text-rose-400 text-xs font-mono">
                <span>Browse</span>
                <ChevronRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </Link>
        </div>
      </section>

      {/* Community CTA */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12 border-t border-gold-500/10">
        <div className="rounded-2xl bg-gradient-to-br from-[#1a150c] via-[#221c10] to-[#120e08] border border-gold-400/35 p-8 sm:p-10 text-center relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-gold-400/10 rounded-full blur-2xl pointer-events-none" />
          <div className="relative z-10">
            <div className="flex items-center justify-center gap-1.5 text-gold-400 text-[11px] font-bold uppercase tracking-widest mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              Aura Community
            </div>
            <h3 className="font-serif text-xl sm:text-2xl font-bold text-white mb-2">
              Join the Conversation
            </h3>
            <p className="text-xs sm:text-sm text-zinc-400 max-w-lg mx-auto mb-6">
              Connect with fellow enthusiasts, share reviews, and get exclusive access to product drops.
            </p>
            <Link
              href="/community"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-gold-gradient text-black font-extrabold text-xs uppercase tracking-wider shadow-gold hover:opacity-95 transition-all group"
            >
              <span>Enter Community</span>
              <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </section>

      {/* Virtual Mall CTA */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12 border-t border-gold-500/10">
        <div className="rounded-2xl bg-gradient-to-br from-[#0a1525] via-[#090b0e] to-[#1a0d16] border border-cyan-500/20 p-8 sm:p-10 text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(34,211,238,0.08)_0%,_transparent_70%)] pointer-events-none" />
          <div className="relative z-10">
            <div className="flex items-center justify-center gap-1.5 text-cyan-400 text-[11px] font-bold uppercase tracking-widest mb-2">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
              </svg>
              3D Virtual Mall
            </div>
            <h3 className="font-serif text-xl sm:text-2xl font-bold text-white mb-2">
              Immersive Shopping Experience
            </h3>
            <p className="text-xs sm:text-sm text-zinc-400 max-w-lg mx-auto mb-6">
              Walk through our virtual flagship mall, explore boutiques in 3D, and transition seamlessly to 2D shopping.
            </p>
            <Link
              href="/shop"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-cyan-500/20 border border-cyan-400/40 text-cyan-200 font-extrabold text-xs uppercase tracking-wider hover:bg-cyan-500/30 hover:border-cyan-400 transition-all group"
            >
              <span>Enter 3D Mall</span>
              <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </section>

      {/* Luxury Footer */}
      <footer className="border-t border-gold-500/15 bg-[#06070a] py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full border border-gold-400/40 flex items-center justify-center text-gold-400 font-serif font-bold text-sm">
              A
            </div>
            <div>
              <p className="font-serif text-base font-bold text-gold-gradient uppercase">
                Aura Bell
              </p>
              <p className="text-[10px] text-zinc-500 tracking-widest uppercase">
                Shop Beyond Limits • Multi-Vendor Platform
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-xs text-zinc-400">
            <Link href="/best-gadget" className="hover:text-gold-300 transition-colors">
              Best Gadget
            </Link>
            <Link href="/aura-skin-care" className="hover:text-gold-300 transition-colors">
              Aura Skin Care
            </Link>
            <Link href="/shop/cart" className="hover:text-gold-300 transition-colors">
              Cart
            </Link>
            <Link href="/account" className="hover:text-gold-300 transition-colors">
              Account
            </Link>
            <Link href="/community" className="hover:text-gold-300 transition-colors">
              Community
            </Link>
          </div>

          <p className="text-xs text-zinc-600">
            &copy; {new Date().getFullYear()} Aura Bell. All rights reserved.
          </p>
        </div>
      </footer>

      {/* Mobile Thumb-Zone Bottom Navigation Bar */}
      <MobileBottomBar />
    </div>
  );
}