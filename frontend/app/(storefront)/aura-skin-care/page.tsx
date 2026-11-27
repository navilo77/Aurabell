"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { ProductGrid } from "@/components/product-grid";
import { Hero2D } from "@/components/hero-2d";
import { ProductRead, StoreRead } from "@/lib/types";
import { getStoreConfig } from "@/lib/stores";
import { Shield, Sparkles, Flower2, ArrowRight, Layers, Tag, Grid, List, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface PriceCalculationRead {
  selling_price: number;
  final_price: number;
}

const STORE_SLUG = "aura-skin-care";

export default function AuraSkinCarePage() {
  const [products, setProducts] = useState<ProductRead[]>([]);
  const [stores, setStores] = useState<StoreRead[]>([]);
  const [selectedStoreId, setSelectedStoreId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prices, setPrices] = useState<Record<string, number>>({});

  useEffect(() => {
    let mounted = true;

    Promise.all([
      apiFetch<ProductRead[]>("/products"),
      apiFetch<StoreRead[]>("/stores"),
    ])
      .then(async ([productsData, storesData]) => {
        if (!mounted) return;
        setProducts(productsData ?? []);
        setStores(storesData ?? []);

        const skinCareStore = storesData?.find((s) => s.slug === STORE_SLUG);
        if (skinCareStore) {
          setSelectedStoreId(skinCareStore.id);
        }

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
  }, []);

  const storeConfig = getStoreConfig(stores, STORE_SLUG);
  const productsWithPrice = products.map((p) => ({
    ...p,
    price: prices[p.id],
    compareAtPrice: undefined,
  }));

  const filteredProducts = productsWithPrice.filter((p) => {
    const store = stores.find((s) => s.id === p.store_id);
    return store?.slug === STORE_SLUG;
  });

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-rose-400 border-t-transparent" />
          <p className="text-xs text-zinc-400 uppercase tracking-widest font-mono">
            Loading Aura Skin Care...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-6 text-center max-w-md mx-auto">
          <p className="text-xs text-rose-300">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {/* Store-Specific Hero Banner */}
      <div className="-mt-8 -mx-4 sm:-mx-6 lg:-mx-8">
        <Hero2D
          stores={stores}
          selectedStoreId={selectedStoreId}
          onSelectStore={setSelectedStoreId}
        />
      </div>

      {/* Store Identity Banner */}
      {storeConfig && (
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-6 p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-[#e11d48]/20 via-[#1f0d16] to-[#0c0e14] border border-[#fda4af]/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xl">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#e11d48]/30 border border-[#fda4af]/60 flex items-center justify-center text-rose-300">
                <Flower2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-serif text-base font-bold text-white flex items-center gap-2">
                  {storeConfig.name} Official Boutique
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#e11d48]/40 text-rose-200">
                    Verified
                  </span>
                </h3>
                <p className="text-xs text-rose-300">{storeConfig.description}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 sm:ml-auto">
              <Link
                href="/community"
                className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-rose-500/15 border border-rose-400/30 text-rose-200 hover:bg-rose-500/25 transition-all"
              >
                <Layers className="w-3 h-3" />
                <span>Community</span>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Category Navigation Tabs */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2 overflow-x-auto pb-2 -mx-4 px-4">
            {[
              { id: "all", label: "All", icon: Grid },
              { id: "serums", label: "Serums", icon: Flower2 },
              { id: "creams", label: "Creams", icon: Tag },
              { id: "cleansers", label: "Cleansers", icon: Sparkles },
              { id: "treatments", label: "Treatments", icon: Layers },
            ].map((cat) => (
              <button
                key={cat.id}
                className={cn(
                  "flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold tracking-wide whitespace-nowrap transition-all",
                  cat.id === "all"
                    ? "bg-rose-500/20 text-rose-200 border border-rose-400/40"
                    : "text-zinc-400 hover:text-white hover:bg-white/5 border border-transparent"
                )}
              >
                <cat.icon className="w-3.5 h-3.5" />
                <span>{cat.label}</span>
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1">
            <button
              className="p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-white/5 transition-colors"
              aria-label="Grid view"
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              className="p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-white/5 transition-colors"
              aria-label="List view"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Trust Strip */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="bg-[#0a0c11] border-y border-rose-500/10 py-2.5">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-center sm:justify-between gap-2 sm:gap-0">
            <div className="flex items-center gap-2 justify-center">
              <Shield className="w-4 h-4 text-rose-400 flex-shrink-0" />
              <p className="text-[11px] font-semibold text-zinc-300">Dermatologist Tested</p>
            </div>
            <div className="hidden sm:block w-px h-4 bg-white/10" />
            <div className="flex items-center gap-2 justify-center">
              <Layers className="w-4 h-4 text-rose-400 flex-shrink-0" />
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
      </div>

      {/* Product Grid */}
      <ProductGrid
        products={filteredProducts as ProductRead[]}
        stores={stores}
        selectedStoreId={selectedStoreId}
        onStoreSelect={setSelectedStoreId}
      />

      {/* CTA to Best Gadget */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pb-12">
        <Link
          href="/best-gadget"
          className="group block p-6 rounded-2xl bg-gradient-to-r from-[#0a121c] via-[#0c1a2e] to-[#0a121c] border border-cyan-500/30 hover:border-cyan-400 hover:shadow-[0_0_25px_rgba(34,211,238,0.25)] transition-all"
        >
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4 text-center sm:text-left">
              <div className="w-14 h-14 rounded-xl bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300">
                <Sparkles className="w-7 h-7" />
              </div>
              <div>
                <h4 className="font-serif text-lg font-bold text-white">Also Explore Best Gadget</h4>
                <p className="text-xs text-cyan-300">Smart tech, smartphones & accessories</p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-cyan-400 group-hover:translate-x-1 transition-transform flex-shrink-0" />
          </div>
        </Link>
      </div>
    </div>
  );
}