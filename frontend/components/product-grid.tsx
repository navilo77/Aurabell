"use client";

import { useState, useMemo } from "react";
import { ProductCard } from "@/components/product-card";
import { ProductRead, StoreRead } from "@/lib/types";
import { LayoutGrid, List, SlidersHorizontal, Sparkles, Store } from "lucide-react";

interface ProductGridProps {
  products: ProductRead[];
  stores: StoreRead[];
  selectedStoreId: string | null;
  onStoreSelect: (storeId: string | null) => void;
  storeSlug?: string;
}

export function ProductGrid({
  products,
  stores,
  selectedStoreId,
  onStoreSelect,
  storeSlug,
}: ProductGridProps) {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  const filteredProducts = useMemo(() => {
    if (!selectedStoreId) return products;
    return products.filter((p) => p.store_id === selectedStoreId);
  }, [products, selectedStoreId]);

  const storeMap = new Map(stores.map((s) => [s.id, s.name]));

  return (
    <div id="marketplace-catalog" className="grid grid-cols-1 lg:grid-cols-12 gap-8">
      {/* Sidebar — Store Directory (only on global pages, not store-scoped) */}
      {!storeSlug && (
        <aside className="lg:col-span-3">
          <div className="sticky top-24 space-y-6">
            {/* Store Filter Card */}
            <div className="rounded-2xl border border-gold-500/20 bg-[#0e1117] p-5 shadow-xl">
              <div className="flex items-center gap-2 mb-4 pb-3 border-b border-gold-500/15">
                <SlidersHorizontal className="h-4 w-4 text-gold-400" />
                <h3 className="font-serif text-sm font-bold uppercase tracking-wider text-gold-gradient">
                  Boutique Directory
                </h3>
              </div>

              <div className="space-y-1.5">
                <button
                  onClick={() => onStoreSelect(null)}
                  className={`w-full text-left rounded-xl px-4 py-3 text-xs font-semibold tracking-wide transition-all ${
                    selectedStoreId === null
                      ? "bg-gold-500/20 text-[#ffe89e] border border-gold-400/60 shadow-gold"
                      : "text-zinc-400 hover:text-white hover:bg-white/5 border border-transparent"
                  }`}
                >
                  🏛️ All Stores
                </button>
                {stores.map((store) => (
                  <button
                    key={store.id}
                    onClick={() => onStoreSelect(store.id)}
                    className={`w-full flex items-center justify-between text-left rounded-xl px-4 py-3 text-xs font-semibold tracking-wide transition-all ${
                      selectedStoreId === store.id
                        ? "bg-gold-500/20 text-[#ffe89e] border border-gold-400/60 shadow-gold"
                        : "text-zinc-400 hover:text-white hover:bg-white/5 border border-transparent"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Store className="w-3.5 h-3.5 text-gold-400" />
                      <span>{store.name}</span>
                    </div>
                    {store.name.toLowerCase().includes("gadget") && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/30">
                        Tech
                      </span>
                    )}
                    {store.name.toLowerCase().includes("skin") && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-500/30">
                        Beauty
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Promotional Card */}
            <div className="rounded-2xl bg-gradient-to-br from-[#1a150c] via-[#221c10] to-[#120e08] border border-gold-400/35 p-5 text-gold-200 shadow-xl relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-gold-400/10 rounded-full blur-2xl pointer-events-none" />
              <div className="flex items-center gap-1.5 text-gold-400 text-[11px] font-bold uppercase tracking-widest">
                <Sparkles className="w-3.5 h-3.5" />
                Aura Privé Access
              </div>
              <p className="mt-2 font-serif text-base font-bold text-white">
                10% Luxury Welcome Bonus
              </p>
              <p className="mt-1 text-xs text-zinc-400">
                Apply code at checkout on your first order:
              </p>
              <div className="mt-3 inline-block rounded-lg bg-gold-500/20 border border-gold-400/50 px-3.5 py-1.5 text-xs font-mono font-bold text-gold-200 tracking-wider">
                AURA10
              </div>
            </div>
          </div>
        </aside>
      )}

      {/* Main Catalog Area */}
      <main className={storeSlug ? "lg:col-span-12" : "lg:col-span-9"}>
        {/* Dynamic Store Ambient Banner */}
        {selectedStoreId && storeMap.get(selectedStoreId)?.toLowerCase().includes("gadget") ? (
          <div className="mb-6 p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-[#0284c7]/20 via-[#0a1525] to-[#0c0e14] border border-[#0ea5e9]/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xl">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#0284c7]/30 border border-[#0ea5e9]/60 flex items-center justify-center text-cyan-300">
                <Store className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-serif text-base font-bold text-white flex items-center gap-2">
                  Best Gadget Official Boutique
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#0284c7]/40 text-cyan-200">
                    Verified
                  </span>
                </h3>
                <p className="text-xs text-cyan-300">Smart Tech. Better Life. • Official Brand Warranty Guaranteed</p>
              </div>
            </div>
            <button
              onClick={() => onStoreSelect(null)}
              className="text-xs text-zinc-400 hover:text-white underline font-mono"
            >
              Show all stores
            </button>
          </div>
        ) : selectedStoreId && storeMap.get(selectedStoreId)?.toLowerCase().includes("skin") ? (
          <div className="mb-6 p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-[#e11d48]/20 via-[#1f0d16] to-[#0c0e14] border border-[#fda4af]/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xl">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#e11d48]/30 border border-[#fda4af]/60 flex items-center justify-center text-rose-300">
                <Store className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-serif text-base font-bold text-white flex items-center gap-2">
                  Aura Skin Care Official Boutique
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#e11d48]/40 text-rose-200">
                    Verified
                  </span>
                </h3>
                <p className="text-xs text-rose-300">Glow Naturally. • Dermatologist Tested & Pure Ingredients</p>
              </div>
            </div>
            <button
              onClick={() => onStoreSelect(null)}
              className="text-xs text-zinc-400 hover:text-white underline font-mono"
            >
              Show all stores
            </button>
          </div>
        ) : null}

        {/* Toolbar */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-gold-500/15">
          <div>
            <span className="text-xs text-zinc-400">
              Showing{" "}
              <span className="font-bold text-gold-300">
                {filteredProducts.length}
              </span>{" "}
              Curated Products
            </span>
          </div>

          <div className="flex items-center gap-1 rounded-xl border border-white/10 bg-[#0e1117] p-1">
            <button
              onClick={() => setViewMode("grid")}
              className={`rounded-lg p-2 transition-all ${
                viewMode === "grid"
                  ? "bg-gold-500/20 text-gold-300 border border-gold-400/40 shadow-sm"
                  : "text-zinc-500 hover:text-white"
              }`}
              aria-label="Grid view"
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`rounded-lg p-2 transition-all ${
                viewMode === "list"
                  ? "bg-gold-500/20 text-gold-300 border border-gold-400/40 shadow-sm"
                  : "text-zinc-500 hover:text-white"
              }`}
              aria-label="List view"
            >
              <List className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Product Grid */}
        {filteredProducts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center rounded-2xl border border-gold-500/15 bg-[#0e1117]/60">
            <div className="w-16 h-16 rounded-2xl bg-gold-500/10 border border-gold-400/30 flex items-center justify-center mb-4 text-2xl">
              🏛️
            </div>
            <h3 className="font-serif text-lg font-bold text-zinc-200">
              No products found
            </h3>
            <p className="mt-1 text-xs text-zinc-400 max-w-sm">
              Try selecting a different boutique store or clear your active filter.
            </p>
          </div>
        ) : (
          <div
            className={
              viewMode === "grid"
                ? "grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6"
                : "flex flex-col gap-4"
            }
          >
            {filteredProducts.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                storeName={storeMap.get(product.store_id)}
                storeSlug={storeSlug}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
