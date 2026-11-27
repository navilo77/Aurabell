import { ProductDetailClient } from "@/app/(storefront)/shop/[id]/product-detail-client";
import { ProductRead, StoreRead } from "@/lib/types";
import { apiFetch } from "@/lib/api";

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
  params: { id: string };
}

async function getProductData(productId: string): Promise<{ product: ProductRead | null; stores: StoreRead[]; price: PriceCalculationRead | null }> {
  try {
    const [productData, storesData] = await Promise.all([
      apiFetch<ProductRead>(`/products/${productId}`),
      apiFetch<StoreRead[]>("/stores"),
    ]);

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

export default async function ProductDetailPage({ params }: PageProps) {
  const productId = params.id;
  const { product, stores, price } = await getProductData(productId);

  return <ProductDetailClient initialProduct={product} initialStores={stores} initialPrice={price} productId={productId} />;
}