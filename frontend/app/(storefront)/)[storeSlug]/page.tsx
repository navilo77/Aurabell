import { resolveStoreBySlug, resolveStoreProducts } from "@/lib/store-resolver";
import { StoreRead, ProductRead } from "@/lib/types";
import { ProductGrid } from "@/components/product-grid";
import { apiFetch } from "@/lib/api";
import React from "react";

export const dynamic = "force-dynamic";

interface PriceCalculationRead {
  selling_price: number;
  final_price: number;
}

interface PageProps {
  params: { storeSlug: string };
}

async function getFeaturedProducts(store: StoreRead): Promise<ProductRead[]> {
  const result = await resolveStoreProducts(store, { per_page: 8, sort: "newest" });
  return result?.data ?? [];
}

async function getStoreCategorySlugs(store: StoreRead): Promise<string[]> {
  try {
    const products = await apiFetch<ProductRead[]>(
      `/products?store_id=${store.id}&per_page=100`
    );
    const categoryIds = new Set(
      products.map((p) => p.category_id).filter(Boolean) as string[]
    );
    return Array.from(categoryIds);
  } catch {
    return [];
  }
}

export default async function StoreHomePage({ params }: PageProps) {
  const store = await resolveStoreBySlug(params.storeSlug);

  const [featuredProducts, categoryIds] = await Promise.all([
    getFeaturedProducts(store),
    getStoreCategorySlugs(store),
  ]);

  return (
    <div className="space-y-10">
      {/* Store Identity Banner */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-6 p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-[var(--store-primary, #d4af37)]/20 via-[#1f1a12] to-[#0c0e14] border border-[var(--store-primary, #d4af37)]/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xl" style={{ "--store-primary": store.primary_color ?? "#d4af37" }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[var(--store-primary, #d4af37)]/30 border border-[var(--store-primary, #d4af37)]/60 flex items-center justify-center" style={{ "--store-primary": store.primary_color ?? "#d4af37" }}>
              {store.primary_color?.includes("cyan") || store.primary_color?.includes("blue") ? (
                <svg className="w-5 h-5 text-cyan-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" /></svg>
              ) : (
                <svg className="w-5 h-5 text-rose-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 11c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" /></svg>
              )}
            </div>
            <div>
              <h3 className="font-serif text-base font-bold text-white flex items-center gap-2">
                {store.name} Official Boutique
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[var(--store-primary, #d4af37)]/40 text-[var(--store-primary, #d4af37)]" style={{ "--store-primary": store.primary_color ?? "#d4af37" }}>
                  Verified
                </span>
              </h3>
              <p className="text-xs" style={{ color: store.primary_color ?? "#d4af37" }}>
                {store.description ?? "Explore our curated collection."}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Category Navigation Tabs - Link to actual category routes */}
      {categoryIds.length > 0 && (
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2 overflow-x-auto pb-2 -mx-4 px-4">
              <a
                href={`/${params.storeSlug}/products`}
                className="flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold tracking-wide whitespace-nowrap transition-all bg-gold-500/20 text-[#ffe89e] border border-gold-400/40"
              >
                <span>All</span>
              </a>
              {categoryIds.map((catId) => (
                <a
                  key={catId}
                  href={`/${params.storeSlug}/categories/${catId}`}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold tracking-wide whitespace-nowrap transition-all text-zinc-400 hover:text-white hover:bg-white/5 border border-transparent"
                >
                  <span>{catId.charAt(0).toUpperCase() + catId.slice(1).replace(/-/g, " ")}</span>
                </a>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Trust Strip */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="bg-[#0a0c11] border-y border-gold-500/10 py-2.5">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-center sm:justify-between gap-2 sm:gap-0">
            <div className="flex items-center gap-2 justify-center">
              <svg className="w-4 h-4 text-gold-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
              <p className="text-[11px] font-semibold text-zinc-300">Genuine Products Guaranteed</p>
            </div>
            <div className="hidden sm:block w-px h-4 bg-white/10" />
            <div className="flex items-center gap-2 justify-center">
              <svg className="w-4 h-4 text-gold-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18a2 2 0 012 2v9a2 2 0 01-2 2H3a2 2 0 01-2-2v-9a2 2 0 012-2z" /><path d="M1 6h22" /><path d="M3 10h18" /></svg>
              <p className="text-[11px] font-semibold text-zinc-300">Shared Multi-Store Cart</p>
            </div>
            <div className="hidden sm:block w-px h-4 bg-white/10" />
            <div className="flex items-center gap-2 justify-center">
              <svg className="w-4 h-4 text-emerald-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6 0a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a6 6 0 016 0m6 0a2 2 0 10-4 0m-4 0a6 6 0 01-6 0" /></svg>
              <p className="text-[11px] font-semibold text-zinc-300">Cash on Delivery (COD)</p>
            </div>
          </div>
        </div>
      </div>

      {/* Featured Products */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <h2 className="font-serif text-2xl font-bold text-white mb-6">Featured Products</h2>
        <ProductGrid
          products={featuredProducts}
          stores={[{ ...store }] as StoreRead[]}
          selectedStoreId={store.id}
          onStoreSelect={() => {}}
          storeSlug={params.storeSlug}
        />
      </div>
    </div>
  );
}