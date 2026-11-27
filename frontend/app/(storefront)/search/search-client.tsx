"use client";

import { useEffect, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { ProductGrid } from "@/components/product-grid";
import { ProductRead, StoreRead, PaginatedResponse } from "@/lib/types";
import { Loader2, Filter, X, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PriceCalculationRead {
  selling_price: number;
  final_price: number;
}

export function SearchPageClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [products, setProducts] = useState<ProductRead[]>([]);
  const [stores, setStores] = useState<StoreRead[]>([]);
  const [selectedStoreId, setSelectedStoreId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prices, setPrices] = useState<Record<string, number>>({});
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    per_page: 20,
    total_pages: 1,
    has_next: false,
    has_prev: false,
  });
  const [sort, setSort] = useState<string>("newest");
  const [minPrice, setMinPrice] = useState<string>("");
  const [maxPrice, setMaxPrice] = useState<string>("");

  const initialQuery = searchParams?.get("q") || "";
  const initialStore = searchParams?.get("store") || "";
  const initialCategory = searchParams?.get("category") || "";
  const initialBrand = searchParams?.get("brand") || "";
  const initialSort = searchParams?.get("sort") || "";
  const initialMinPrice = searchParams?.get("min_price") || "";
  const initialMaxPrice = searchParams?.get("max_price") || "";
  const initialPage = parseInt(searchParams?.get("page") || "1", 10);

  useEffect(() => {
    if (initialSort) setSort(initialSort);
    if (initialMinPrice) setMinPrice(initialMinPrice);
    if (initialMaxPrice) setMaxPrice(initialMaxPrice);
  }, [initialSort, initialMinPrice, initialMaxPrice]);

  const fetchProducts = useCallback(async (page: number = 1) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: "20",
        format: "v2",
      });
      if (initialQuery) params.append("search", initialQuery);
      if (initialCategory) params.append("category_id", initialCategory);
      if (initialBrand) params.append("brand", initialBrand);
      if (initialStore) params.append("store_id", initialStore);
      if (sort) params.append("sort", sort);
      if (minPrice) params.append("min_price", minPrice);
      if (maxPrice) params.append("max_price", maxPrice);

      const data = await apiFetch<PaginatedResponse<ProductRead>>(`/products?${params.toString()}`);
      if (data) {
        setProducts(data.data);
        setPagination(data.meta);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [initialQuery, initialCategory, initialBrand, initialStore, sort, minPrice, maxPrice]);

  const fetchStores = useCallback(async () => {
    try {
      const data = await apiFetch<StoreRead[]>("/stores");
      setStores(data ?? []);
      if (initialStore) {
        const store = data?.find((s) => s.id === initialStore);
        if (store) setSelectedStoreId(store.id);
      }
    } catch {
      // Ignore
    }
  }, [initialStore]);

  useEffect(() => {
    fetchProducts(initialPage);
    fetchStores();
  }, [fetchProducts, fetchStores, initialPage]);

  const productsWithPrice = products.map((p) => ({
    ...p,
    price: prices[p.id],
    compareAtPrice: undefined,
  }));

  const filteredProducts = selectedStoreId
    ? productsWithPrice.filter((p) => {
        const store = stores.find((s) => s.id === p.store_id);
        return store?.id === selectedStoreId;
      })
    : productsWithPrice;

  const handleSortChange = (newSort: string) => {
    setSort(newSort);
    const params = new URLSearchParams(searchParams.toString());
    params.set("sort", newSort);
    params.set("page", "1");
    router.push(`/search?${params.toString()}`);
  };

  const handlePriceFilter = () => {
    const params = new URLSearchParams(searchParams.toString());
    if (minPrice) params.set("min_price", minPrice);
    else params.delete("min_price");
    if (maxPrice) params.set("max_price", maxPrice);
    else params.delete("max_price");
    params.set("page", "1");
    router.push(`/search?${params.toString()}`);
  };

  const handleClearFilters = () => {
    const params = new URLSearchParams();
    if (initialQuery) params.set("q", initialQuery);
    if (initialCategory) params.set("category", initialCategory);
    if (initialBrand) params.set("brand", initialBrand);
    router.push(`/search?${params.toString()}`);
  };

  const sortOptions = [
    { value: "newest", label: "নতুনতম" },
    { value: "price_asc", label: "দাম: কম থেকে বেশি" },
    { value: "price_desc", label: "দাম: বেশি থেকে কম" },
    { value: "name_asc", label: "নাম: ক-খ" },
    { value: "name_desc", label: "নাম: খ-ক" },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <nav className="flex items-center gap-1 text-sm text-muted-foreground mb-6">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-1 hover:text-primary transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
            স্পর্শ করে ফিরে যান
          </button>
          <span>/</span>
          <span className="text-foreground">Search</span>
        </nav>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar - Filters */}
          <aside className="lg:col-span-1">
            <div className="sticky top-24 space-y-6">
              {/* Search Query Display */}
              {initialQuery && (
                <div className="rounded-xl border border-gold-500/20 bg-[#0e1117] p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Filter className="h-4 w-4 text-gold-400" />
                    <h3 className="font-serif text-sm font-bold text-gold-gradient">Search Results</h3>
                  </div>
                  <p className="text-sm text-zinc-200">&ldquo;{initialQuery}&rdquo;</p>
                  <p className="text-xs text-zinc-400 mt-1">{pagination.total} products found</p>
                </div>
              )}

              {/* Store Filter */}
              <div className="rounded-xl border border-gold-500/20 bg-[#0e1117] p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Filter className="h-4 w-4 text-gold-400" />
                  <h3 className="font-serif text-sm font-bold text-gold-gradient">Boutique</h3>
                </div>
                <div className="space-y-1.5">
                  <button
                    onClick={() => {
                      const params = new URLSearchParams(searchParams.toString());
                      params.delete("store");
                      params.set("page", "1");
                      router.push(`/search?${params.toString()}`);
                    }}
                    className={`w-full text-left rounded-xl px-4 py-3 text-xs font-semibold tracking-wide transition-all ${
                      !selectedStoreId && !initialStore
                        ? "bg-gold-500/20 text-[#ffe89e] border border-gold-400/60 shadow-gold"
                        : "text-zinc-400 hover:text-white hover:bg-white/5 border border-transparent"
                    }`}
                  >
                    🏛️ All Stores
                  </button>
                  {stores.map((store) => (
                    <button
                      key={store.id}
                      onClick={() => {
                        const params = new URLSearchParams(searchParams.toString());
                        params.set("store", store.id);
                        params.set("page", "1");
                        router.push(`/search?${params.toString()}`);
                      }}
                      className={`w-full flex items-center justify-between text-left rounded-xl px-4 py-3 text-xs font-semibold tracking-wide transition-all ${
                        selectedStoreId === store.id || initialStore === store.id
                          ? "bg-gold-500/20 text-[#ffe89e] border border-gold-400/60 shadow-gold"
                          : "text-zinc-400 hover:text-white hover:bg-white/5 border border-transparent"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span>🏪</span>
                        <span>{store.name}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Sort */}
              <div className="rounded-xl border border-gold-500/20 bg-[#0e1117] p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Filter className="h-4 w-4 text-gold-400" />
                  <h3 className="font-serif text-sm font-bold text-gold-gradient">Sort By</h3>
                </div>
                <select
                  value={sort}
                  onChange={(e) => handleSortChange(e.target.value)}
                  className="w-full h-10 px-3 rounded-xl bg-[#141824] border border-white/10 text-xs text-white focus:outline-none focus:border-gold-400"
                >
                  {sortOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Price Range */}
              <div className="rounded-xl border border-gold-500/20 bg-[#0e1117] p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Filter className="h-4 w-4 text-gold-400" />
                  <h3 className="font-serif text-sm font-bold text-gold-gradient">Price Range</h3>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="number"
                    placeholder="Min"
                    value={minPrice}
                    onChange={(e) => setMinPrice(e.target.value)}
                    className="h-10 px-3 rounded-xl bg-[#141824] border border-white/10 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-gold-400"
                  />
                  <input
                    type="number"
                    placeholder="Max"
                    value={maxPrice}
                    onChange={(e) => setMaxPrice(e.target.value)}
                    className="h-10 px-3 rounded-xl bg-[#141824] border border-white/10 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-gold-400"
                  />
                </div>
                <button
                  onClick={handlePriceFilter}
                  className="w-full mt-3 h-10 rounded-xl bg-gold-gradient text-black font-bold text-xs uppercase tracking-wider"
                >
                  Apply
                </button>
              </div>

              {/* Clear Filters */}
              {(selectedStoreId || initialStore || sort !== "newest" || minPrice || maxPrice) && (
                <button
                  onClick={handleClearFilters}
                  className="w-full h-10 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-300 text-xs font-bold uppercase tracking-wider hover:bg-rose-500/20"
                >
                  <X className="w-3.5 h-3.5 mr-1.5" />
                  Clear All Filters
                </button>
              )}
            </div>
          </aside>

          {/* Main Results */}
          <main className="lg:col-span-3">
            <div className="mb-6">
              <h1 className="font-serif text-2xl sm:text-3xl font-extrabold text-white">
                {initialQuery ? `Results for &ldquo;{initialQuery}&rdquo;` : "Search Products"}
              </h1>
              <p className="text-xs text-zinc-400 mt-1">
                {pagination.total} product{pagination.total !== 1 ? "s" : ""} found
              </p>
            </div>

            {error && (
              <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-6 text-center max-w-lg mx-auto mb-6">
                <p className="text-xs text-rose-300">{error}</p>
              </div>
            )}

            {loading ? (
              <div className="flex flex-col items-center justify-center py-20">
                <Loader2 className="w-10 h-10 rounded-full border-2 border-gold-400/20 border-t-gold-400 animate-spin mb-3" />
                <p className="text-xs text-gold-300 font-mono tracking-widest uppercase">Loading Products...</p>
              </div>
            ) : filteredProducts.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-center rounded-2xl border border-gold-500/15 bg-[#0e1117]/60">
                <div className="w-16 h-16 rounded-2xl bg-gold-500/10 border border-gold-400/30 flex items-center justify-center mb-4 text-2xl">🏛️</div>
                <h3 className="font-serif text-lg font-bold text-zinc-200">No products found</h3>
                <p className="mt-1 text-xs text-zinc-400 max-w-sm">Try adjusting your filters or search terms.</p>
              </div>
            ) : (
              <>
                <ProductGrid
                  products={filteredProducts as ProductRead[]}
                  stores={stores}
                  selectedStoreId={selectedStoreId}
                  onStoreSelect={setSelectedStoreId}
                />

                {/* Pagination */}
                {pagination.total_pages > 1 && (
                  <div className="flex items-center justify-center gap-2 mt-8">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const params = new URLSearchParams(searchParams.toString());
                        params.set("page", (pagination.page - 1).toString());
                        router.push(`/search?${params.toString()}`);
                      }}
                      disabled={!pagination.has_prev}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm text-muted-foreground">
                      Page {pagination.page} / {pagination.total_pages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const params = new URLSearchParams(searchParams.toString());
                        params.set("page", (pagination.page + 1).toString());
                        router.push(`/search?${params.toString()}`);
                      }}
                      disabled={!pagination.has_next}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}