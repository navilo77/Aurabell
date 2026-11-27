"use client";

import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Search, Sparkles, X, Loader2, ArrowRight } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { ProductRead } from "@/lib/types";

export function LiveSearch() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState(searchParams?.get("q") || "");
  const [results, setResults] = useState<ProductRead[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Handle live matching via backend API
  useEffect(() => {
    if (!query.trim() || query.length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    setLoading(true);
    const timeout = setTimeout(async () => {
      try {
        const params = new URLSearchParams({
          search: query,
          per_page: "5",
        });
        const data = await apiFetch<{ data: ProductRead[] }>(`/products?${params.toString()}`);
        setResults(data?.data ?? []);
        setIsOpen(true);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 200);

    return () => clearTimeout(timeout);
  }, [query]);

  // Click outside listener
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      setIsOpen(false);
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <div ref={containerRef} className="relative w-full max-w-xs sm:max-w-sm">
      <form onSubmit={handleSubmit} className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gold-400/80" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => {
            if (results.length > 0) setIsOpen(true);
          }}
          placeholder="Search in Aura Bell..."
          className="w-full h-9 pl-10 pr-8 text-xs rounded-full bg-[#12161f]/80 backdrop-blur-md border border-white/10 text-white placeholder:text-zinc-400 focus:outline-none focus:border-gold-400/70 focus:ring-1 focus:ring-gold-400/50 transition-all"
        />
        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery("");
              setResults([]);
              setIsOpen(false);
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </form>

      {/* Floating Glass Results Dropdown */}
      {isOpen && (
        <div className="absolute top-11 left-0 right-0 z-50 rounded-2xl bg-[#0c0e14]/95 backdrop-blur-2xl border border-gold-500/30 shadow-2xl p-2 animate-in fade-in zoom-in-95 duration-200">
          {loading ? (
            <div className="p-4 text-center text-xs text-zinc-400 flex items-center justify-center gap-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-gold-400" />
              <span>Searching boutiques...</span>
            </div>
          ) : results.length === 0 ? (
            <div className="p-4 text-center text-xs text-zinc-400">
              No matching products found for <span className="text-gold-300">&ldquo;{query}&rdquo;</span>
            </div>
          ) : (
            <div className="space-y-1">
              <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-gold-400 border-b border-white/5 flex items-center justify-between">
                <span>Matching Products</span>
                <span>{results.length} found</span>
              </div>

              {results.map((product) => {
                const primaryImage =
                  product.images?.find((img) => img.is_primary)?.image_url ??
                  product.images?.[0]?.image_url ??
                  "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=80&h=80&fit=crop";

                const isGadget =
                  product.name.toLowerCase().includes("tech") ||
                  product.name.toLowerCase().includes("phone") ||
                  product.name.toLowerCase().includes("laptop");

                return (
                  <Link
                    key={product.id}
                    href={`/shop/${product.id}`}
                    onClick={() => setIsOpen(false)}
                    className="flex items-center gap-3 p-2 rounded-xl hover:bg-white/5 transition-colors group"
                  >
                    <div className="relative w-10 h-10 rounded-lg overflow-hidden bg-black flex-shrink-0 border border-white/5">
                      <Image
                        src={primaryImage}
                        alt={product.name}
                        fill
                        className="object-cover group-hover:scale-105 transition-transform"
                      />
                    </div>

                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-zinc-200 truncate group-hover:text-gold-300">
                        {product.name}
                      </p>
                      <span
                        className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${
                          isGadget
                            ? "bg-cyan-950/80 text-cyan-300 border border-cyan-500/30"
                            : "bg-rose-950/80 text-rose-300 border border-rose-500/30"
                        }`}
                      >
                        {isGadget ? "Best Gadget" : "Aura Skin Care"}
                      </span>
                    </div>

                    <ArrowRight className="w-3.5 h-3.5 text-zinc-500 group-hover:text-gold-400 group-hover:translate-x-0.5 transition-all" />
                  </Link>
                );
              })}

              <button
                type="button"
                onClick={handleSubmit}
                className="w-full mt-1 p-2 rounded-xl text-center text-xs font-bold text-gold-300 hover:bg-gold-500/10 transition-colors flex items-center justify-center gap-1 border-t border-white/5"
              >
                <span>View all results for &ldquo;{query}&rdquo;</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}