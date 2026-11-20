"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { ProductRead, StoreRead } from "@/lib/types";
import { ProductGrid } from "@/components/product-grid";

export default function SuperAdminCatalogPage() {
  const [products, setProducts] = useState<ProductRead[]>([]);
  const [stores, setStores] = useState<StoreRead[]>([]);
  const [selectedStoreId, setSelectedStoreId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiFetch<ProductRead[]>("/admin/products"),
      apiFetch<StoreRead[]>("/stores"),
    ])
      .then(([productsData, storesData]) => {
        setProducts(productsData);
        setStores(storesData);
      })
      .catch(() => {
        setProducts([]);
        setStores([]);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground">Global Catalog</h1>
        <p className="text-muted-foreground">View and manage all products across all stores</p>
      </div>
      <ProductGrid
        products={products}
        stores={stores}
        selectedStoreId={selectedStoreId}
        onStoreSelect={setSelectedStoreId}
      />
    </div>
  );
}