"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { ShoppingCart, Eye, Sparkles, Check, Loader2, ShieldCheck, Award } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useToast } from "@/components/ui/toast";

interface ProductCardProps {
  product: {
    id: string;
    store_id: string;
    name: string;
    slug: string;
    description: string | null;
    images: { image_url: string; is_primary: boolean }[];
    variants: { id?: string; sku: string; variant_name: string | null }[];
    store?: { name: string };
    price?: number;
    compareAtPrice?: number;
  };
  storeName?: string;
  storeSlug?: string;
  href?: string;
}

export function ProductCard({ product, storeName, storeSlug, href }: ProductCardProps) {
  const { toast } = useToast();
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);

  const getCuratedImage = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes("iphone") || n.includes("phone")) {
      return "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=600&auto=format&fit=crop&q=80";
    }
    if (n.includes("macbook") || n.includes("laptop")) {
      return "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&auto=format&fit=crop&q=80";
    }
    if (n.includes("wash") || n.includes("vitamin") || n.includes("serum") || n.includes("skin") || n.includes("cream")) {
      return "https://images.unsplash.com/photo-1608248597359-20c2d3a3d69a?w=600&auto=format&fit=crop&q=80";
    }
    if (n.includes("headphone") || n.includes("audio") || n.includes("earphone")) {
      return "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80";
    }
    return "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=600&auto=format&fit=crop&q=80";
  };

  const primaryImage =
    product.images?.find((img) => img.is_primary)?.image_url ??
    product.images?.[0]?.image_url ??
    getCuratedImage(product.name);

  const resolvedStoreName = product.store?.name ?? storeName ?? "Aura Boutique";

  const isGadget =
    resolvedStoreName.toLowerCase().includes("gadget") ||
    product.name.toLowerCase().includes("tech") ||
    product.name.toLowerCase().includes("phone") ||
    product.name.toLowerCase().includes("laptop");

  const isSkinCare =
    resolvedStoreName.toLowerCase().includes("skin") ||
    resolvedStoreName.toLowerCase().includes("aura") ||
    product.name.toLowerCase().includes("cream") ||
    product.name.toLowerCase().includes("serum");

  const resolvedHref = storeSlug ? `/${storeSlug}/products/${product.id}` : (href ?? `/shop/${product.id}`);

  const handleQuickAdd = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const firstVariant = product.variants?.[0];
    if (!firstVariant) {
      window.location.href = resolvedHref;
      return;
    }

    setAdding(true);
    try {
      await apiFetch("/cart/items", {
        method: "POST",
        body: JSON.stringify({
          variant_id: firstVariant.id,
          quantity: 1,
        }),
      });
      setAdded(true);
      window.dispatchEvent(new Event("cart-updated"));
      window.dispatchEvent(new Event("open-cart-drawer"));
      toast({
        title: "Added to Cart",
        description: `${product.name} added to your shared cart.`,
      });
      setTimeout(() => setAdded(false), 2000);
    } catch (err: any) {
      toast({
        title: "Cart",
        description: err.message || "Failed to add item to cart.",
      });
    } finally {
      setAdding(false);
    }
  };

  const discountPercent =
    product.compareAtPrice && product.price && product.compareAtPrice > product.price
      ? Math.round(((product.compareAtPrice - product.price) / product.compareAtPrice) * 100)
      : null;

  return (
    <article
      className={`group relative flex flex-col rounded-3xl overflow-hidden transition-all duration-500 border ${
        isGadget
          ? "bg-[#0b0f17] border-[#0ea5e9]/25 hover:border-[#0ea5e9]/70 hover:shadow-[0_10px_35px_-5px_rgba(14,165,233,0.3)]"
          : isSkinCare
          ? "bg-[#140c12] border-[#fda4af]/25 hover:border-[#fda4af]/70 hover:shadow-[0_10px_35px_-5px_rgba(251,113,133,0.3)]"
          : "bg-[#0f1118] border-gold-500/25 hover:border-gold-400/70 hover:shadow-[0_10px_35px_-5px_rgba(212,175,55,0.3)]"
      }`}
    >
      <Link href={resolvedHref} className="block flex-1 flex flex-col">
        {/* Editorial Portrait Image Section (4:5 Ratio) */}
        <div className="relative aspect-[4/5] overflow-hidden bg-[#161a24]">
          <Image
            src={primaryImage}
            alt={product.name}
            fill
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
            className="object-cover transition-transform duration-700 ease-out group-hover:scale-106"
          />

          {/* Luxury Vignette & Dark Ambient Overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30 opacity-70 group-hover:opacity-40 transition-opacity duration-300" />

          {/* Top-Right Badge: Discount or Variant Count */}
          <div className="absolute top-3.5 right-3.5 flex flex-col items-end gap-1.5 z-10">
            {discountPercent ? (
              <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-rose-600 text-white shadow-lg">
                {discountPercent}% OFF
              </span>
            ) : product.variants.length > 0 ? (
              <span className="px-2.5 py-1 rounded-full text-[10px] font-medium bg-black/70 backdrop-blur-md text-zinc-300 border border-white/10 shadow-sm">
                {product.variants.length} Edition{product.variants.length !== 1 ? "s" : ""}
              </span>
            ) : null}
          </div>

          {/* Top-Left Store Brand Tag */}
          <div className="absolute top-3.5 left-3.5 z-10">
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider backdrop-blur-md shadow-md ${
                isGadget
                  ? "bg-[#0284c7]/30 border border-[#0ea5e9]/60 text-cyan-200"
                  : isSkinCare
                  ? "bg-[#e11d48]/30 border border-[#fda4af]/60 text-rose-200"
                  : "bg-gold-500/25 border border-gold-400/60 text-gold-200"
              }`}
            >
              <Sparkles className="w-3 h-3 text-gold-400" />
              {resolvedStoreName}
            </span>
          </div>

          {/* Bottom Floating Spec Pill (Editorial Magazine Highlight) */}
          <div className="absolute bottom-3 left-3 right-3 z-10">
            <div className="px-3 py-1.5 rounded-xl bg-black/60 backdrop-blur-md border border-white/10 flex items-center justify-between text-[10px] text-zinc-300">
              <span className="flex items-center gap-1 font-mono">
                {isGadget ? (
                  <>
                    <ShieldCheck className="w-3 h-3 text-cyan-400" />
                    <span>Official Distributor Warranty</span>
                  </>
                ) : isSkinCare ? (
                  <>
                    <Award className="w-3 h-3 text-rose-300" />
                    <span>Dermatologist Certified</span>
                  </>
                ) : (
                  <>
                    <Check className="w-3 h-3 text-gold-400" />
                    <span>100% Genuine Guaranteed</span>
                  </>
                )}
              </span>
              <span className="text-zinc-500 font-bold">&rsaquo;</span>
            </div>
          </div>
        </div>

        {/* Editorial Content Section */}
        <div className="p-5 flex flex-col gap-2.5 flex-1 justify-between bg-gradient-to-b from-transparent to-black/30">
          <div>
            <h3 className="font-serif font-bold text-base text-zinc-100 line-clamp-1 group-hover:text-gold-300 transition-colors">
              {product.name}
            </h3>
            <p className="text-xs text-zinc-400 line-clamp-2 mt-1 leading-relaxed">
              {product.description ?? "Curated luxury craftsmanship verified by Aura Bell."}
            </p>
          </div>

          <div className="flex items-center justify-between pt-3.5 border-t border-white/10">
            <div className="flex flex-col">
              <div className="flex items-baseline gap-1.5">
                <span className="text-lg sm:text-xl font-serif font-black text-gold-gradient tracking-tight">
                  ৳{((typeof product.price === "number" ? product.price : Number(product.price)) ?? 0).toFixed(2)}
                </span>
                {product.compareAtPrice && product.compareAtPrice > (product.price ?? 0) && (
                  <span className="text-xs text-zinc-500 line-through font-mono">
                    ৳{((typeof product.compareAtPrice === "number" ? product.compareAtPrice : Number(product.compareAtPrice)) ?? 0).toFixed(2)}
                  </span>
                )}
              </div>
              <span className="text-[10px] text-zinc-500 font-medium">VAT included</span>
            </div>

            <button
              onClick={handleQuickAdd}
              disabled={adding}
              className={`min-h-[42px] px-4 py-2 rounded-full text-xs font-bold transition-all flex items-center gap-2 shadow-md active:scale-95 ${
                added
                  ? "bg-emerald-600 text-white"
                  : isGadget
                  ? "bg-[#0284c7]/25 border border-[#0ea5e9]/60 text-cyan-200 hover:bg-[#0284c7]/40 hover:shadow-[0_0_15px_rgba(2,132,199,0.5)]"
                  : isSkinCare
                  ? "bg-[#e11d48]/25 border border-[#fda4af]/60 text-rose-200 hover:bg-[#e11d48]/40 hover:shadow-[0_0_15px_rgba(225,29,72,0.5)]"
                  : "bg-gold-500/25 border border-gold-400/60 text-gold-300 hover:bg-gold-500/40 hover:shadow-gold"
              }`}
              title="Add to shared cart"
            >
              {adding ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : added ? (
                <>
                  <Check className="w-4 h-4" />
                  <span>Added</span>
                </>
              ) : (
                <>
                  <ShoppingCart className="w-4 h-4" />
                  <span>Add to Cart</span>
                </>
              )}
            </button>
          </div>
        </div>
      </Link>
    </article>
  );
}
