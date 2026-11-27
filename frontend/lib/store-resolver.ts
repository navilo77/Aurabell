import { StoreRead } from "@/lib/types";
import { apiFetchOptional } from "@/lib/api";
import { notFound } from "next/navigation";

export async function resolveStoreBySlug(slug: string): Promise<StoreRead> {
  const store = await apiFetchOptional<StoreRead>(`/stores/${slug}`);
  if (!store) {
    notFound();
  }
  if (store.status !== "active") {
    notFound();
  }
  return store;
}

export async function resolveStoreProducts(
  store: StoreRead,
  options?: { category?: string; page?: number; per_page?: number; sort?: string }
): Promise<{ data: any[]; meta: any } | null> {
  const params = new URLSearchParams();
  params.set("store_id", store.id);
  if (options?.category) params.set("category", options.category);
  if (options?.page) params.set("page", options.page.toString());
  if (options?.per_page) params.set("per_page", options.per_page.toString());
  if (options?.sort) params.set("sort", options.sort);
  params.set("format", "v2");

  return apiFetchOptional<any>(`/products?${params.toString()}`);
}

export async function resolveProductInStore(
  store: StoreRead,
  productId: string
): Promise<any | null> {
  const product = await apiFetchOptional<any>(`/products/${productId}`);
  if (!product) return null;

  if (product.store_id !== store.id) {
    return null;
  }

  return product;
}