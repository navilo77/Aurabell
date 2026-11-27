import { resolveStoreBySlug, resolveStoreProducts } from "@/lib/store-resolver";
import { StoreRead, ProductRead, PaginatedResponse } from "@/lib/types";
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
  searchParams: { category?: string; page?: string; sort?: string };
}

export default async function StoreProductsPage({ params, searchParams }: PageProps) {
  const { storeSlug } = params;
  const { category, page = "1", sort } = searchParams;
  const store = await resolveStoreBySlug(storeSlug);

  const productsResult = await resolveStoreProducts(store, {
    category,
    page: parseInt(page, 10),
    per_page: 20,
    sort,
  });

  const products = productsResult?.data ?? [];
  const pagination = productsResult?.meta ?? {
    total: 0,
    page: 1,
    per_page: 20,
    total_pages: 1,
    has_next: false,
    has_prev: false,
  };

  const productsWithPrice = await Promise.all(
    products.map(async (p: ProductRead) => {
      if (p.variants && p.variants.length > 0) {
        try {
          const priceData = await apiFetch<PriceCalculationRead>(
            `/pricing/calculate?variant_id=${p.variants[0].id}&store_id=${p.store_id}`
          );
          const rawPrice = priceData.final_price ?? priceData.selling_price;
          return {
            ...p,
            price: typeof rawPrice === "number" ? rawPrice : Number(rawPrice) || 0,
            compareAtPrice: undefined,
          };
        } catch {
          return { ...p, price: 0, compareAtPrice: undefined };
        }
      }
      return { ...p, price: 0, compareAtPrice: undefined };
    })
  );

  const sortOptions = [
    { value: "newest", label: "Newest" },
    { value: "price_asc", label: "Price: Low to High" },
    { value: "price_desc", label: "Price: High to Low" },
    { value: "name_asc", label: "Name: A-Z" },
    { value: "name_desc", label: "Name: Z-A" },
  ];

  return (
    <div className="space-y-10">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="font-serif text-2xl sm:text-3xl font-bold text-white">
              All Products — {store.name}
            </h1>
            <p className="text-xs text-zinc-400">{pagination.total} products found</p>
          </div>
          <select
            defaultValue={sort || "newest"}
            onChange={(e) => {
              const params = new URLSearchParams();
              if (category) params.set("category", category);
              params.set("sort", e.target.value);
              params.set("page", "1");
              window.location.href = `/${storeSlug}/products?${params.toString()}`;
            }}
            className="h-10 px-3 rounded-xl bg-[#141824] border border-white/10 text-xs text-white focus:outline-none focus:border-gold-400"
          >
            {sortOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

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

      {productsWithPrice.length === 0 ? (
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-center py-20 text-center rounded-2xl border border-gold-500/15 bg-[#0e1117]/60">
            <div className="w-16 h-16 rounded-2xl bg-gold-500/10 border border-gold-400/30 flex items-center justify-center mb-4 text-2xl">🏛️</div>
            <h3 className="font-serif text-lg font-bold text-zinc-200">No products found</h3>
            <p className="mt-1 text-xs text-zinc-400 max-w-sm">Try adjusting your filters or search terms.</p>
          </div>
        </div>
      ) : (
        <>
          <ProductGrid
            products={productsWithPrice as ProductRead[]}
            stores={[{ ...store }] as StoreRead[]}
            selectedStoreId={store.id}
            onStoreSelect={() => {}}
            storeSlug={params.storeSlug}
          />

          {pagination.total_pages > 1 && (
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex items-center justify-center gap-2 mt-8">
              <a
                href={pagination.has_prev ? `/${storeSlug}/products?${new URLSearchParams({ category: category ?? "", page: (pagination.page - 1).toString(), sort: sort ?? "" }).toString()}` : "#"}
                className={`h-10 px-4 rounded-xl border border-white/10 bg-[#141824] text-xs text-white hover:bg-white/5 transition-colors ${!pagination.has_prev ? "pointer-events-none opacity-50" : ""}`}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
              </a>
              <span className="text-sm text-muted-foreground">
                Page {pagination.page} / {pagination.total_pages}
              </span>
              <a
                href={pagination.has_next ? `/${storeSlug}/products?${new URLSearchParams({ category: category ?? "", page: (pagination.page + 1).toString(), sort: sort ?? "" }).toString()}` : "#"}
                className={`h-10 px-4 rounded-xl border border-white/10 bg-[#141824] text-xs text-white hover:bg-white/5 transition-colors ${!pagination.has_next ? "pointer-events-none opacity-50" : ""}`}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
              </a>
            </div>
          )}
        </>
      )}
    </div>
  );
}