"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { StoreRead } from "@/lib/types";
import Link from "next/link";

export default function SuperAdminStoresPage() {
  const [stores, setStores] = useState<StoreRead[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<StoreRead[]>("/stores")
      .then((data) => setStores(data))
      .catch(() => setStores([]))
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = () => {
    // Would clear auth and redirect
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b bg-background">
        <div className="flex items-center justify-between px-4 py-4 lg:px-8">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-primary">Super Admin</h1>
            <span className="text-muted-foreground">|</span>
            <span className="text-sm text-muted-foreground">Manage Stores</span>
          </div>
        </div>
      </div>

      <div className="flex">
        <aside className="w-64 bg-background border-r min-h-screen p-4">
          <nav className="space-y-2">
            <Link
              href="/super-admin"
              className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-primary"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-8 0h2" />
              </svg>
              Dashboard
            </Link>
            <Link
              href="/super-admin/stores"
              className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium bg-primary text-primary-foreground"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
              Manage Stores
            </Link>
            <Link
              href="/super-admin/catalog"
              className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-primary"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4m-4 0h16v6H4v-6zm4 0v6m6-6v6" />
              </svg>
              Global Catalog
            </Link>
          </nav>
        </aside>

        <main className="flex-1 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">Manage Stores</h2>
            <Link
              href="/super-admin/stores/new"
              className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
            >
              + Create Store
            </Link>
          </div>

          <div className="space-y-4">
            {loading ? (
              <p className="text-muted-foreground">Loading...</p>
            ) : stores.length > 0 ? (
              <div>
                {stores.map((store) => (
                  <div key={store.id} className="rounded-lg border border-border bg-card p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium">{store.name}</h3>
                        <p className="text-sm text-muted-foreground">{store.slug}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/super-admin/stores/${store.id}/edit`}
                          className="text-sm text-primary hover:text-primary/80"
                        >
                          Edit
                        </Link>
                        <Link
                          href={`/super-admin/stores/${store.id}`}
                          className="text-sm text-muted-foreground hover:text-primary"
                        >
                          View
                        </Link>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-lg border border-border bg-card p-8 text-center">
                <p className="text-muted-foreground">No stores yet. Create your first store!</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}