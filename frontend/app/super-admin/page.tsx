"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { ProductRead, StoreRead } from "@/lib/types";
import { ProductCard } from "@/components/product-card";
import { LayoutDashboard, Users, Globe } from "lucide-react";

export default function SuperAdminPage() {
  const [products, setProducts] = useState<ProductRead[]>([]);
  const [stores, setStores] = useState<StoreRead[]>([]);
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

  const activeStores = stores.filter((s) => s.status === "active").length;

  return (
    <div className="flex">
      <aside className="w-64 shrink-0 border-r bg-background p-4 min-h-[calc(100vh-4rem)]">
        <nav className="space-y-2">
          <Link
            href="/super-admin"
            className="flex items-center gap-3 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground"
          >
            <LayoutDashboard className="h-4 w-4" />
            Dashboard
          </Link>
          <Link
            href="/super-admin/stores"
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-primary"
          >
            <Users className="h-4 w-4" />
            Manage Stores
          </Link>
          <Link
            href="/super-admin/catalog"
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-primary"
          >
            <Globe className="h-4 w-4" />
            Global Catalog
          </Link>
        </nav>
      </aside>

      <main className="flex-1 p-6">
        <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
        <p className="text-muted-foreground mb-6">Platform overview across all stores.</p>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          <div className="rounded-lg border border-border bg-card p-4">
            <h3 className="text-sm font-medium text-muted-foreground">Total Products</h3>
            <p className="mt-2 text-3xl font-bold text-primary">{products.length}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <h3 className="text-sm font-medium text-muted-foreground">Total Stores</h3>
            <p className="mt-2 text-3xl font-bold text-primary">{stores.length}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <h3 className="text-sm font-medium text-muted-foreground">Active Stores</h3>
            <p className="mt-2 text-3xl font-bold text-primary">{activeStores}</p>
          </div>
        </div>

        <h2 className="mt-8 text-xl font-semibold text-foreground">Recent Products</h2>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {loading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : products.length > 0 ? (
            products.slice(0, 6).map((product) => (
              <ProductCard key={product.id} product={product} storeName="Store" />
            ))
          ) : (
            <p className="text-muted-foreground">No products in the catalog yet.</p>
          )}
        </div>
      </main>
    </div>
  );
}