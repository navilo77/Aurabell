"use client";

import Link from "next/link";

export default function StoreAdminOrdersPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="border-b bg-background">
        <div className="flex items-center justify-between px-4 py-4 lg:px-8">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-primary">Store Admin</h1>
            <span className="text-muted-foreground">|</span>
            <span className="text-sm text-muted-foreground">Orders</span>
          </div>
        </div>
      </div>

      <div className="flex">
        <aside className="w-64 bg-background border-r min-h-screen p-4">
          <nav className="space-y-2">
            <Link
              href="/store-admin"
              className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-primary"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-8 0h2" />
              </svg>
              Dashboard
            </Link>
            <Link
              href="/store-admin/products"
              className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-primary"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
              Products
            </Link>
            <Link
              href="/store-admin/orders"
              className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium bg-primary text-primary-foreground"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4m-4 0h16v6H4v-6zm4 0v6m6-6v6" />
              </svg>
              Orders
            </Link>
          </nav>
        </aside>

        <main className="flex-1 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">Orders</h2>
          </div>

          <div className="rounded-lg border border-border bg-card p-6 text-center">
            <p className="text-muted-foreground">No orders yet. Orders will appear here when customers purchase from your store.</p>
          </div>
        </main>
      </div>
    </div>
  );
}