import { resolveStoreBySlug, resolveProductInStore } from "@/lib/store-resolver";
import { StoreRead, ProductRead } from "@/lib/types";
import { ProductDetailClient } from "@/app/(storefront)/shop/[id]/product-detail-client";
import { apiFetch } from "@/lib/api";

export const dynamic = "force-dynamic";

interface PriceCalculationRead {
  variant_id: string;
  store_id: string;
  currency_code: string;
  selling_price: number;
  compare_at_price: number | null;
  discount_amount: number;
  final_price: number;
  promotion_id: string | null;
  coupon_code: string | null;
}

interface PageProps {
  params: { storeSlug: string; id: string };
}

async function getProductData(productId: string, storeId: string): Promise<{ product: ProductRead | null; stores: StoreRead[]; price: PriceCalculationRead | null }> {
  try {
    const [productData, storesData] = await Promise.all([
      apiFetch<ProductRead>(`/products/${productId}`),
      apiFetch<StoreRead[]>("/stores"),
    ]);

    if (productData.store_id !== storeId) {
      return { product: null, stores: [], price: null };
    }

    let priceData: PriceCalculationRead | null = null;
    if (productData.variants.length > 0) {
      try {
        priceData = await apiFetch<PriceCalculationRead>(
          `/pricing/calculate?variant_id=${productData.variants[0].id}&store_id=${productData.store_id}`
        );
      } catch {
        priceData = null;
      }
    }

    return { product: productData, stores: storesData, price: priceData };
  } catch {
    return { product: null, stores: [], price: null };
  }
}

export default async function StoreProductDetailPage({ params }: PageProps) {
  const { storeSlug, id: productId } = params;
  const store = await resolveStoreBySlug(storeSlug);

  const product = await resolveProductInStore(store, productId);

  if (!product) {
    const { notFound } = await import("next/navigation");
    notFound();
  }

  const { product: fullProduct, stores, price } = await getProductData(productId, store.id);

  if (!fullProduct) {
    const { notFound } = await import("next/navigation");
    notFound();
  }

  return <ProductDetailClient initialProduct={fullProduct} initialStores={stores} initialPrice={price} productId={productId} />;
}