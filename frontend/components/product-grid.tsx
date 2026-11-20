"use client";

import { useState, useMemo } from "react";
import { ProductCard } from "@/components/product-card";
import { ProductRead, StoreRead } from "@/lib/types";
import { LayoutGrid, List, SlidersHorizontal } from "lucide-react";

interface ProductGridProps {
  products: ProductRead[];
  stores: StoreRead[];
  selectedStoreId: string | null;
  onStoreSelect: (storeId: string | null) => void;
}

export function ProductGrid({
  products,
  stores,
  selectedStoreId,
  onStoreSelect,
}: ProductGridProps) {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  const filteredProducts = useMemo(() => {
    if (!selectedStoreId) return products;
    return products.filter((p) => p.store_id === selectedStoreId);
  }, [products, selectedStoreId]);

  const storeMap = new Map(stores.map((s) => [s.id, s.name]));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
      {/* সাইডবার — ফিল্টার */}
      <aside className="lg:col-span-3">
        <div className="sticky top-24 space-y-6">
          {/* স্টোর ফিল্টার */}
          <div className="rounded-2xl border border-border bg-card p-5">
            <div className="flex items-center gap-2 mb-4">
              <SlidersHorizontal className="h-4 w-4 text-muted-foreground" />
              <h3 className="text-sm font-semibold text-foreground">
                স্টোর দিয়ে ফিল্টার
              </h3>
            </div>
            <div className="space-y-1.5">
              <button
                onClick={() => onStoreSelect(null)}
                className={`w-full text-left rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all ${
                  selectedStoreId === null
                    ? "bg-gradient-to-r from-[hsl(262,83%,58%)] to-[hsl(290,70%,55%)] text-white shadow-md shadow-primary/25"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                }`}
              >
                সব স্টোর (All Stores)
              </button>
              {stores.map((store) => (
                <button
                  key={store.id}
                  onClick={() => onStoreSelect(store.id)}
                  className={`w-full text-left rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all ${
                    selectedStoreId === store.id
                      ? "bg-gradient-to-r from-[hsl(262,83%,58%)] to-[hsl(290,70%,55%)] text-white shadow-md shadow-primary/25"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  }`}
                >
                  {store.name}
                </button>
              ))}
            </div>
          </div>

          {/* প্রমোশনাল কার্ড */}
          <div className="rounded-2xl bg-gradient-to-br from-[hsl(262,83%,58%)] to-[hsl(290,70%,55%)] p-5 text-white">
            <p className="text-xs font-semibold uppercase tracking-wider opacity-80">
              Special Offer
            </p>
            <p className="mt-2 text-lg font-bold">
              নতুন কাস্টমারদের জন্য ১০% ছাড়!
            </p>
            <p className="mt-1 text-sm opacity-80">
              প্রথম অর্ডারে কোড ব্যবহার করুন
            </p>
            <div className="mt-3 inline-block rounded-lg bg-white/20 backdrop-blur-sm px-3 py-1.5 text-sm font-mono font-bold">
              AURA10
            </div>
          </div>
        </div>
      </aside>

      {/* মেইন কন্টেন্ট */}
      <main className="lg:col-span-9">
        {/* টুলবার */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <span className="text-sm text-muted-foreground">
              <span className="font-semibold text-foreground">
                {filteredProducts.length}
              </span>{" "}
              পণ্য পাওয়া গেছে
            </span>
          </div>
          <div className="flex items-center gap-1 rounded-xl border border-border bg-card p-1">
            <button
              onClick={() => setViewMode("grid")}
              className={`rounded-lg p-2 transition-all ${
                viewMode === "grid"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
              aria-label="Grid view"
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`rounded-lg p-2 transition-all ${
                viewMode === "list"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
              aria-label="List view"
            >
              <List className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* প্রোডাক্ট গ্রিড */}
        {filteredProducts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-16 h-16 rounded-2xl bg-accent flex items-center justify-center mb-4">
              <span className="text-2xl">🔍</span>
            </div>
            <p className="text-lg font-semibold text-foreground mb-1">
              কোনো পণ্য পাওয়া যায়নি
            </p>
            <p className="text-sm text-muted-foreground">
              অন্য ফিল্টার ব্যবহার করে দেখুন
            </p>
          </div>
        ) : viewMode === "grid" ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5">
            {filteredProducts.map((product) => {
              const store = stores.find((s) => s.id === product.store_id);
              return (
                <ProductCard
                  key={product.id}
                  product={product}
                  storeName={store?.name ?? undefined}
                />
              );
            })}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredProducts.map((product) => {
              const store = stores.find((s) => s.id === product.store_id);
              return (
                <ProductCard
                  key={product.id}
                  product={product}
                  storeName={store?.name ?? undefined}
                />
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
