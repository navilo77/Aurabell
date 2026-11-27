"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { ProductGrid } from "@/components/product-grid";
import { ProductRead, StoreRead } from "@/lib/types";
import { getStoreConfig, getStoreConfigById } from "@/lib/stores";
import { ChevronLeft } from "lucide-react";
import { useRouter, useParams } from "next/navigation";

interface PriceCalculationRead {
  selling_price: number;
  final_price: number;
}

const STORE_SLUG = "best-gadget";

export default function BestGadgetCategoryPage() {
  const router = useRouter();
  const params = useParams();
  const categorySlug = params.slug as string;
  const [products, setProducts] = useState<ProductRead[]>([]);
  const [stores, setStores] = useState<StoreRead[]>([]);
  const [selectedStoreId, setSelectedStoreId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prices, setPrices] = useState<Record<string, number>>({});

  useEffect(() => {
    let mounted = true;

    Promise.all([
      apiFetch<ProductRead[]>(`/products?category=${categorySlug}`),
      apiFetch<StoreRead[]>("/stores"),
    ])
      .then(async ([productsData, storesData]) => {
        if (!mounted) return;
        setProducts(productsData ?? []);
        setStores(storesData ?? []);

        const bestGadgetStore = storesData?.find((s) => s.slug === STORE_SLUG);
        if (bestGadgetStore) {
          setSelectedStoreId(bestGadgetStore.id);
        }

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
  }, [categorySlug]);

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

  const handleBack = () => router.back();

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-cyan-400 border-t-transparent" />
          <p className="text-xs text-zinc-400 uppercase tracking-widest font-mono">
            Loading Category...
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
          <button onClick={handleBack} className="mt-4 text-sm text-cyan-300 hover:underline">
            ← Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {/* Category Header */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-4 mb-6">
          <button onClick={handleBack} className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors">
            <ChevronLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back</span>
          </button>
          <div>
            <h1 className="font-serif text-2xl sm:text-3xl font-bold text-white">
              {categorySlug.charAt(0).toUpperCase() + categorySlug.slice(1).replace(/-/g, " ")}
            </h1>
            <p className="text-xs text-zinc-400">{filteredProducts.length} products found</p>
          </div>
        </div>
      </div>

      {/* Store Identity Banner */}
      {storeConfig && (
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-6 p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-[#0284c7]/20 via-[#0a1525] to-[#0c0e14] border border-[#0ea5e9]/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xl">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#0284c7]/30 border border-[#0ea5e9]/60 flex items-center justify-center text-cyan-300">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                </svg>
              </div>
              <div>
                <h3 className="font-serif text-base font-bold text-white flex items-center gap-2">
                  {storeConfig.name} Official Boutique
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#0284c7]/40 text-cyan-200">
                    Verified
                  </span>
                </h3>
                <p className="text-xs text-cyan-300">{storeConfig.description}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Product Grid */}
      <ProductGrid
        products={filteredProducts as ProductRead[]}
        stores={stores}
        selectedStoreId={selectedStoreId}
        onStoreSelect={setSelectedStoreId}
      />
    </div>
  );
}