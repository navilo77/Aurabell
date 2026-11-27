"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { ProductRead } from "@/lib/types";
import Link from "next/link";
import { ProductCard } from "@/components/product-card";
import { LayoutDashboard, Package, ShoppingBag } from "lucide-react";

export default function StoreAdminPage() {
  const [products, setProducts] = useState<ProductRead[]>([]);
  const [loading, setLoading] = useState(true);
  const { logout } = useAuth();

  useEffect(() => {
    apiFetch<ProductRead[]>("/admin/products")
      .then((data) => setProducts(data))
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = async () => {
    await logout();
    window.location.href = "/login";
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b bg-background">
        <div className="flex items-center justify-between px-4 py-4 lg:px-8">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-primary">Store Admin</h1>
            <span className="text-muted-foreground">|</span>
            <span className="text-sm text-muted-foreground">Manage your store</span>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={handleLogout}
              className="px-3 py-2 text-sm font-medium rounded-md border border-input bg-background hover:bg-accent"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>

      <div className="flex">
        <aside className="w-64 bg-background border-r min-h-screen p-4">
          <nav className="space-y-2">
            <Link
              href="/store-admin"
              className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium bg-primary text-primary-foreground"
            >
              <LayoutDashboard className="h-4 w-4" />
              Dashboard
            </Link>
            <Link
              href="/store-admin/products"
              className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-primary"
            >
              <Package className="h-4 w-4" />
              Products
            </Link>
            <Link
              href="/store-admin/orders"
              className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-primary"
            >
              <ShoppingBag className="h-4 w-4" />
              Orders
            </Link>
          </nav>
        </aside>

        <main className="flex-1 p-6">
          <h2 className="text-2xl font-bold mb-4">Dashboard</h2>
          <p className="text-muted-foreground mb-6">
            Welcome back! Here&apos;s an overview of your store.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="rounded-lg border border-border bg-card p-4">
              <h3 className="text-sm font-medium text-muted-foreground">Total Products</h3>
              <p className="text-3xl font-bold text-primary mt-2">{products.length}</p>
            </div>
            <div className="rounded-lg border border-border bg-card p-4">
              <h3 className="text-sm font-medium text-muted-foreground">Active Products</h3>
              <p className="text-3xl font-bold text-primary mt-2">
                {products.filter((p) => p.status === "active").length}
              </p>
            </div>
            <div className="rounded-lg border border-border bg-card p-4">
              <h3 className="text-sm font-medium text-muted-foreground">Draft Products</h3>
              <p className="text-3xl font-bold text-primary mt-2">
                {products.filter((p) => p.status === "draft").length}
              </p>
            </div>
          </div>

          <h3 className="text-xl font-semibold mt-8 mb-4">Recent Products</h3>
          {loading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : products.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {products.slice(0, 6).map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  storeName="Your Store"
                />
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No products yet. Create your first product!</p>
          )}
        </main>
      </div>
    </div>
  );
}