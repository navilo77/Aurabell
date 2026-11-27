import { resolveStoreBySlug, resolveStoreProducts } from "@/lib/store-resolver";
import { StoreRead, ProductRead } from "@/lib/types";
import { ProductGrid } from "@/components/product-grid";
import { ChevronLeft } from "lucide-react";
import { apiFetch } from "@/lib/api";
import React from "react";

export const dynamic = "force-dynamic";

interface PriceCalculationRead {
  selling_price: number;
  final_price: number;
}

interface PageProps {
  params: { storeSlug: string; slug: string };
}

export default async function StoreCategoryPage({ params }: PageProps) {
  const { storeSlug, slug: categoryId } = params;
  const store = await resolveStoreBySlug(storeSlug);

  const productsResult = await resolveStoreProducts(store, { category: categoryId });
  const products = productsResult?.data ?? [];

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

  const categoryTitle = categoryId.charAt(0).toUpperCase() + categoryId.slice(1).replace(/-/g, " ");

  return (
    <div className="space-y-10">
      {/* Category Header */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-4 mb-6">
          <a
            href={`/${storeSlug}`}
            className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back</span>
          </a>
          <div>
            <h1 className="font-serif text-2xl sm:text-3xl font-bold text-white">
              {categoryTitle}
            </h1>
            <p className="text-xs text-zinc-400">{productsWithPrice.length} products found</p>
          </div>
        </div>
      </div>

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

      {/* Product Grid */}
      <ProductGrid
        products={productsWithPrice as ProductRead[]}
        stores={[{ ...store }] as StoreRead[]}
        selectedStoreId={store.id}
        onStoreSelect={() => {}}
        storeSlug={params.storeSlug}
      />
    </div>
  );
}