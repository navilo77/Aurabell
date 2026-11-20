import { ShoppingCart, Eye } from "lucide-react";

interface ProductCardProps {
  product: {
    id: string;
    store_id: string;
    name: string;
    slug: string;
    description: string | null;
    images: { image_url: string; is_primary: boolean }[];
    variants: { sku: string; variant_name: string | null }[];
    store?: { name: string };
  };
  storeName?: string;
}

export function ProductCard({ product, storeName }: ProductCardProps) {
  const primaryImage =
    product.images.find((img) => img.is_primary)?.image_url ??
    product.images[0]?.image_url ??
    "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop";

  return (
    <article className="group relative flex flex-col rounded-2xl border border-border bg-card overflow-hidden card-hover">
      {/* ছবি সেকশন */}
      <div className="relative aspect-[4/3] overflow-hidden bg-muted">
        <img
          src={primaryImage}
          alt={product.name}
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
        />
        {/* ওভারলে গ্র্যাডিয়েন্ট */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

        {/* হোভারে দেখা যাবে — কুইক অ্যাকশন বাটন */}
        <div className="absolute inset-0 flex items-center justify-center gap-3 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-2 group-hover:translate-y-0">
          <button className="w-10 h-10 rounded-full bg-white/90 backdrop-blur-sm flex items-center justify-center text-foreground hover:bg-white hover:scale-110 transition-all shadow-lg" aria-label="Quick view">
            <Eye className="h-4 w-4" />
          </button>
          <button className="w-10 h-10 rounded-full bg-gradient-to-r from-[hsl(262,83%,58%)] to-[hsl(290,70%,55%)] flex items-center justify-center text-white hover:scale-110 transition-all shadow-lg" aria-label="Add to cart">
            <ShoppingCart className="h-4 w-4" />
          </button>
        </div>

        {/* ভ্যারিয়েন্ট ব্যাজ */}
        <div className="absolute top-3 right-3">
          <span className="inline-flex items-center rounded-full bg-white/90 backdrop-blur-sm px-2.5 py-1 text-xs font-medium text-foreground shadow-sm">
            {product.variants.length} variant{product.variants.length !== 1 ? "s" : ""}
          </span>
        </div>

        {/* স্টোর ব্যাজ */}
        <div className="absolute top-3 left-3">
          <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-[hsl(262,83%,58%)] to-[hsl(290,70%,55%)] px-2.5 py-1 text-xs font-medium text-white shadow-sm">
            {storeName ?? product.store?.name ?? "Store"}
          </span>
        </div>
      </div>

      {/* তথ্য সেকশন */}
      <div className="p-4 flex flex-col gap-2 flex-1">
        <h3 className="font-semibold text-foreground line-clamp-1 group-hover:text-[hsl(262,83%,58%)] transition-colors">
          {product.name}
        </h3>
        <p className="text-sm text-muted-foreground line-clamp-2 flex-1">
          {product.description ?? "No description available."}
        </p>

        <div className="flex items-center justify-between mt-2 pt-3 border-t border-border/50">
          <div className="flex items-baseline gap-1">
            <span className="text-lg font-bold text-gradient">৳0.00</span>
          </div>
          <button className="flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1.5 text-xs font-semibold text-[hsl(262,83%,58%)] hover:bg-primary/20 transition-colors">
            <ShoppingCart className="h-3.5 w-3.5" />
            কার্টে যোগ
          </button>
        </div>
      </div>
    </article>
  );
}
