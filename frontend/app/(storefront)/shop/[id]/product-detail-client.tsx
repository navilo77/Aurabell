"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ShoppingCart,
  Mail,
  Phone,
  MapPin,
  Clock,
  Tag,
  Image as ImageIcon,
  Plus,
  Minus,
  ChevronLeft,
  ArrowRight,
  Star,
  Loader2,
  Package,
  Truck,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ProductRead, VariantRead, ImageRead, StoreRead } from "@/lib/types";
import Image from "next/image";
import { useToast } from "@/components/ui/toast";

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

interface ProductDetailClientProps {
  initialProduct: ProductRead | null;
  initialStores: StoreRead[];
  initialPrice: PriceCalculationRead | null;
  productId: string;
}

export function ProductDetailClient({ initialProduct, initialStores, initialPrice, productId }: ProductDetailClientProps) {
  const router = useRouter();
  const { toast } = useToast();

  const [product, setProduct] = useState<ProductRead | null>(initialProduct);
  const [stores, setStores] = useState<StoreRead[]>(initialStores);
  const [selectedVariant, setSelectedVariant] = useState<VariantRead | null>(null);
  const [price, setPrice] = useState<PriceCalculationRead | null>(initialPrice);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(!initialProduct);
  const [error, setError] = useState<string | null>(initialProduct ? null : "পণ্য পাওয়া যায়নি");
  const [addingToCart, setAddingToCart] = useState(false);

  const fetchProduct = useCallback(async () => {
    try {
      setLoading(true);
      const [productData, storesData] = await Promise.all([
        apiFetch<ProductRead>(`/products/${productId}`),
        apiFetch<StoreRead[]>("/stores"),
      ]);
      setProduct(productData);
      setStores(storesData);

      if (productData.variants.length > 0) {
        setSelectedVariant(productData.variants[0]);
        await fetchPrice(productData.variants[0].id, productData.store_id);
      }
    } catch (e: any) {
      setError(e.message || "পণ্য লোড করতে সমস্যা হচ্ছে");
      toast({ title: "ভুল", description: e.message || "পণ্য লোড করতে সমস্যা হচ্ছে", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [productId, toast]);

  const fetchPrice = async (variantId: string, storeId: string) => {
    try {
      const priceData = await apiFetch<PriceCalculationRead>(
        `/pricing/calculate?variant_id=${variantId}&store_id=${storeId}`
      );
      setPrice(priceData);
    } catch {
      setPrice(null);
    }
  };

  const handleAddToCart = async () => {
    if (!selectedVariant || !product) return;
    setAddingToCart(true);
    try {
      await apiFetch(`/cart/items`, {
        method: "POST",
        body: JSON.stringify({
          variant_id: selectedVariant.id,
          quantity,
        }),
      });
      window.dispatchEvent(new Event("cart-updated"));
      window.dispatchEvent(new Event("open-cart-drawer"));
      toast({
        title: "Added to Cart",
        description: `${product.name} has been added to your cart.`,
      });
    } catch (e: any) {
      toast({ title: "ভুল", description: e.message || "কার্টে যোগ করতে সমস্যা হচ্ছে", variant: "destructive" });
    } finally {
      setAddingToCart(false);
    }
  };

  const store = stores.find((s) => s.id === product?.store_id);
  const primaryImage = product?.images.find((img) => img.is_primary)?.image_url ?? product?.images[0]?.image_url;
  const toNum = (v: unknown): number => (typeof v === "number" ? v : Number(v)) || 0;
  const sellingPrice = toNum(price?.selling_price);
  const compareAtPrice = price?.compare_at_price != null ? toNum(price.compare_at_price) : null;
  const finalPrice = toNum(price?.final_price);
  const discountAmount = toNum(price?.discount_amount);

  useEffect(() => {
    if (!initialProduct) {
      fetchProduct();
    }
  }, [fetchProduct, initialProduct]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">পণ্য লোড হচ্ছে...</p>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-destructive">{error || "পণ্য পাওয়া যায়নি"}</h2>
          <Button onClick={() => router.back()} className="mt-4">
            ফিরে যান
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-8 lg:px-8">
        <nav className="flex items-center gap-1 text-sm text-muted-foreground mb-6">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-1 hover:text-primary transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
            স্পর্শ করে ফিরে যান
          </button>
          <span>/</span>
          <span className="cursor-pointer hover:text-primary transition-colors">শপ</span>
          <span>/</span>
          <span className="text-foreground">{product.name}</span>
        </nav>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* ইমেজ গ্যালারি */}
          <div className="lg:col-span-5 space-y-6">
            <div
              className={`aspect-[4/5] rounded-2xl border border-border bg-muted overflow-hidden relative ${!primaryImage ? "flex items-center justify-center" : ""}`}
            >
              {primaryImage ? (
                <Image src={primaryImage} alt={product.name} fill className="object-cover" />
              ) : (
                <div className="h-full w-full flex items-center justify-center text-muted-foreground">
                  <ImageIcon className="h-12 w-12 opacity-50" />
                </div>
              )}
              {/* থাম্বনেইল */}
              {product.images.length > 1 && (
                <div className="absolute inset-0 flex items-end justify-center p-2 pb-4 gap-2 bg-gradient-to-t from-black/60 to-transparent">
                  {product.images.map((img, idx) => (
                    <button
                      key={img.id}
                      onClick={() => {}}
                      className="h-8 w-8 rounded-md border border-border/50 bg-background/90 hover:bg-primary hover:text-primary-foreground transition-all"
                    >
                      <div className="h-6 w-6 rounded-sm overflow-hidden border border-white/30">
                        <Image src={img.image_url} alt="" fill className="object-cover" />
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* ছোট থাম্বনেইল সারি */}
            <div className="flex gap-2 overflow-x-auto pb-2">
              {product.images.map((img, idx) => (
                <button
                  key={img.id}
                  onClick={() => {}}
                  className="shrink-0 h-16 w-16 rounded-xl border border-border bg-muted overflow-hidden hover:border-primary transition-all"
                >
                  <Image src={img.image_url} alt="" fill className="object-cover" />
                </button>
              ))}
            </div>
          </div>

          {/* পণ্যের তথ্য */}
          <div className="lg:col-span-7 space-y-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <Badge variant="outline" className="text-xs">
                  {store?.name || "স্টোর"}
                </Badge>
                <h1 className="text-3xl font-bold text-foreground mt-2 mb-2">{product.name}</h1>
                {product.brand && (
                  <p className="text-sm text-muted-foreground">{product.brand}</p>
                )}
              </div>
              <div className="flex items-end gap-2">
                <Star className="h-5 w-5 text-warning fill-warning" />
                <span className="text-sm font-medium text-foreground">(0 রিভিউ)</span>
              </div>
            </div>

            {/* দাম */}
            <div className="flex items-baseline gap-3">
              <span className="text-3xl font-bold text-foreground">
                ৳{finalPrice.toFixed(2)}
              </span>
              {compareAtPrice && compareAtPrice > finalPrice && (
                <span className="text-lg text-muted-foreground line-through">
                  ৳{compareAtPrice.toFixed(2)}
                </span>
              )}
              {discountAmount > 0 && (
                <Badge variant="success" className="text-xs ml-2">
                  ৳{discountAmount.toFixed(2)} সাশ্রয়
                </Badge>
              )}
            </div>

            {/* ভ্যারিয়েন্ট সিলেকশন */}
            {product.variants.length > 1 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">ভ্যারিয়েন্ট নির্বাচন করুন</CardTitle>
                  <CardDescription>আপনার পছন্দের ভ্যারিয়েন্টটি বেছে নিন</CardDescription>
                </CardHeader>
                <CardContent className="p-4 pt-0">
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                    {product.variants.map((variant) => {
                      const isSelected = selectedVariant?.id === variant.id;
                      return (
                        <button
                          key={variant.id}
                          onClick={() => {
                            setSelectedVariant(variant);
                            setQuantity(1);
                            fetchPrice(variant.id, product.store_id);
                          }}
                          className={cn(
                            "flex flex-col items-center justify-center p-3 rounded-lg border transition-all",
                            isSelected
                              ? "bg-primary text-primary-foreground border-primary shadow-md"
                              : "bg-background border-border text-foreground hover:bg-accent hover:border-primary/30"
                          )}
                        >
                          <span className="text-xs font-medium">{variant.variant_name || variant.attributes.color || variant.attributes.size || "ভ্যারিয়েন্ট"}</span>
                          <span className="text-xs mt-1 text-muted-foreground">{variant.sku}</span>
                        </button>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* পরিমাণ নিয়ন্ত্রণ */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-foreground">পরিমাণ</span>
                <div className="flex items-center border rounded-lg overflow-hidden">
                  <button
                    onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                    disabled={quantity <= 1}
                    className="w-10 h-10 border-r border-border bg-background text-foreground hover:bg-accent disabled:opacity-50"
                  >
                    <Minus className="h-4 w-4" />
                  </button>
                  <span className="w-8 text-center font-medium text-foreground">{quantity}</span>
                  <button
                    onClick={() => setQuantity((q) => q + 1)}
                    className="w-10 h-10 border-l border-border bg-background text-foreground hover:bg-accent"
                  >
                    <Plus className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>

            {/*.ACTION বাটন */}
            <div className="flex gap-3">
              <Button
                onClick={handleAddToCart}
                disabled={addingToCart || !selectedVariant}
                className="flex-1 h-12 bg-gradient-to-r from-[hsl(262,83%,58%)] to-[hsl(290,70%,55%)] text-white font-semibold shadow-lg shadow-primary/25 hover:shadow-lg hover:shadow-primary/40 transition-all"
              >
                {addingToCart ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    যোগ হচ্ছে...
                  </>
                ) : (
                  <>
                    <ShoppingCart className="h-5 w-5 mr-2" />
                    কার্টে যোগ করুন
                  </>
                )}
              </Button>
              <Button variant="outline" className="flex-1 h-12">
                কিনে নিন
              </Button>
            </div>

            {/* বিবরণ */}
            {product.description && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">পণ্যের বিবরণ</CardTitle>
                </CardHeader>
                <CardContent className="p-4 pt-0">
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {product.description}
                  </p>
                </CardContent>
              </Card>
            )}

            {/* স্টোর তথ্য */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">স্টোর</CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-0">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M3 10h18a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2z" />
                      <path d="M1 6h22" />
                      <path d="M3 10h18" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-medium text-foreground">{store?.name || "অজানা স্টোর"}</h3>
                    <p className="text-xs text-muted-foreground">
                      <MapPin className="h-3 w-3 mr-1 inline" /> ঢাকা, বাংলাদেশ
                    </p>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="pt-0">
                <div className="flex items-center gap-2">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">সাপোর্টের জন্য কল করুন</span>
                </div>
              </CardFooter>
            </Card>
          </div>
        </div>

        {/* সংশ্লিষ্ট পণ্য */}
        <div className="mt-16">
          <h2 className="text-2xl font-bold text-foreground mb-6">
            আপনার জন্য পণ্য সুপারিশ
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <ProductCardSkeleton key={i} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ProductCardSkeleton() {
  return (
    <Card className="h-full">
      <div className="h-48 bg-muted rounded-xl mb-4 animate-shimmer" />
      <div className="space-y-2">
        <div className="h-4 bg-muted rounded w-3/4 animate-shimmer" />
        <div className="h-4 bg-muted rounded w-1/2 animate-shimmer" />
        <div className="flex items-center gap-2 mt-2">
          <div className="h-3 bg-muted rounded w-1/3 animate-shimmer" />
          <div className="h-3 bg-muted rounded w-1/3 animate-shimmer" />
        </div>
      </div>
    </Card>
  );
}