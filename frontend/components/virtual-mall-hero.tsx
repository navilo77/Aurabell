"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Compass,
  Sparkles,
  ChevronRight,
  Cpu,
  Flower2,
  Navigation,
  X,
  ShoppingCart,
  Eye,
  Check,
  Building,
  Store,
  Layers,
  MapPin,
} from "lucide-react";
import { ProductRead, StoreRead } from "@/lib/types";
import { apiFetch } from "@/lib/api";
import { useToast } from "@/components/ui/toast";

interface VirtualMallHeroProps {
  stores: StoreRead[];
  products: ProductRead[];
  prices: Record<string, number>;
  onSelectStore: (storeId: string | null) => void;
  selectedStoreId: string | null;
}

type SectorId = "atrium" | "gadget" | "skincare" | "vault";

export function VirtualMallHero({
  stores,
  products,
  prices,
  onSelectStore,
  selectedStoreId,
}: VirtualMallHeroProps) {
  const { toast } = useToast();
  const [activeSector, setActiveSector] = useState<SectorId>("atrium");
  const [spotlightStore, setSpotlightStore] = useState<StoreRead | null>(null);
  const [isMapExpanded, setIsMapExpanded] = useState(false);
  const [isZooming, setIsZooming] = useState(false);
  const [addingId, setAddingId] = useState<string | null>(null);

  // Identify stores
  const bestGadgetStore = stores.find((s) =>
    s.name.toLowerCase().includes("gadget")
  );
  const auraSkinCareStore = stores.find((s) =>
    s.name.toLowerCase().includes("skin") || s.name.toLowerCase().includes("aura")
  );

  // Filter products for spotlight boutique modal
  const spotlightProducts = spotlightStore
    ? products.filter((p) => p.store_id === spotlightStore.id).slice(0, 4)
    : [];

  // Compass needle rotation based on active sector
  const needleRotation =
    activeSector === "gadget"
      ? -48
      : activeSector === "skincare"
      ? 48
      : activeSector === "vault"
      ? 0
      : -12;

  const handleSectorClick = (sector: SectorId) => {
    setActiveSector(sector);
    if (sector === "gadget" && bestGadgetStore) {
      setSpotlightStore(bestGadgetStore);
    } else if (sector === "skincare" && auraSkinCareStore) {
      setSpotlightStore(auraSkinCareStore);
    } else if (sector === "atrium") {
      onSelectStore(null);
      scrollToCatalog();
    }
  };

  const scrollToCatalog = () => {
    setIsZooming(true);
    setTimeout(() => {
      setIsZooming(false);
      const el = document.getElementById("marketplace-catalog");
      if (el) {
        el.scrollIntoView({ behavior: "smooth" });
      }
    }, 450);
  };

  const handleQuickAddToCart = async (product: ProductRead) => {
    const firstVariant = product.variants?.[0];
    if (!firstVariant) return;

    setAddingId(product.id);
    try {
      await apiFetch("/cart/items", {
        method: "POST",
        body: JSON.stringify({
          variant_id: firstVariant.id,
          quantity: 1,
        }),
      });
      toast({
        title: "Added to Cart",
        description: `${product.name} added to your shared cart.`,
      });
    } catch (e: any) {
      toast({
        title: "Cart",
        description: e.message || "Item added to cart.",
      });
    } finally {
      setAddingId(null);
    }
  };

  return (
    <section className="relative w-full h-[94vh] min-h-[620px] max-h-[940px] overflow-hidden select-none bg-[#090b0e]">
      {/* 3D ভার্চুয়াল মল ক্যানভাস (Clean Background with Camera Glide) */}
      <div
        className={`absolute inset-0 transition-transform duration-700 ease-out ${
          isZooming ? "scale-108" : "scale-100"
        }`}
      >
        <Image
          src="/images/virtual-mall.jpg"
          alt="Aura Bell 3D Virtual Luxury Mall"
          fill
          priority
          className="object-cover object-center"
        />

        {/* সিনেমাটিক অ্যাম্বিয়েন্স এবং ভিগনেট ওভারলে */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#090b0e] via-transparent to-black/40 pointer-events-none" />
        <div className="absolute inset-0 bg-gradient-to-r from-black/40 via-transparent to-black/40 pointer-events-none" />
      </div>

      {/* ইন্টারেক্টিভ বুটিক আর্চওয়ে ১: Best Gadget (West Wing / বামে) */}
      <div
        className="absolute left-[5%] top-[25%] w-[28%] sm:w-[22%] h-[42%] z-20 cursor-pointer group"
        onMouseEnter={() => setActiveSector("gadget")}
        onClick={() => {
          if (bestGadgetStore) setSpotlightStore(bestGadgetStore);
          else onSelectStore(null);
        }}
        title="Click to enter Best Gadget Boutique"
      >
        {/* লাক্সারি নিয়ন হ্যালো ইফেক্ট (হোভার করলে দৃশ্যমান) */}
        <div className="absolute inset-0 rounded-3xl border border-cyan-400/0 group-hover:border-cyan-400/50 group-hover:bg-cyan-500/10 group-hover:shadow-[0_0_40px_rgba(34,211,238,0.3)] transition-all duration-400 flex flex-col justify-start items-center p-4">
          <div className="opacity-0 group-hover:opacity-100 transition-all duration-300 transform -translate-y-2 group-hover:translate-y-0 bg-[#0a1018]/90 backdrop-blur-xl px-4 py-2 rounded-full border border-cyan-400/60 flex items-center gap-2.5 shadow-2xl">
            <Cpu className="w-4 h-4 text-cyan-400 animate-pulse" />
            <div className="flex flex-col text-left">
              <span className="text-xs font-bold text-cyan-100">Best Gadget</span>
              <span className="text-[10px] text-cyan-400 font-medium tracking-wide">Enter Boutique &rsaquo;</span>
            </div>
          </div>
        </div>
      </div>

      {/* ইন্টারেক্টিভ বুটিক আর্চওয়ে ২: Aura Skin Care (East Wing / ডানে) */}
      <div
        className="absolute right-[5%] top-[25%] w-[28%] sm:w-[22%] h-[42%] z-20 cursor-pointer group"
        onMouseEnter={() => setActiveSector("skincare")}
        onClick={() => {
          if (auraSkinCareStore) setSpotlightStore(auraSkinCareStore);
          else onSelectStore(null);
        }}
        title="Click to enter Aura Skin Care Boutique"
      >
        {/* লাক্সারি রোজ গোল্ড হ্যালো ইফেক্ট */}
        <div className="absolute inset-0 rounded-3xl border border-rose-400/0 group-hover:border-rose-400/50 group-hover:bg-rose-500/10 group-hover:shadow-[0_0_40px_rgba(251,113,133,0.3)] transition-all duration-400 flex flex-col justify-start items-center p-4">
          <div className="opacity-0 group-hover:opacity-100 transition-all duration-300 transform -translate-y-2 group-hover:translate-y-0 bg-[#170c12]/90 backdrop-blur-xl px-4 py-2 rounded-full border border-rose-400/60 flex items-center gap-2.5 shadow-2xl">
            <Flower2 className="w-4 h-4 text-rose-300 animate-pulse" />
            <div className="flex flex-col text-left">
              <span className="text-xs font-bold text-rose-100">Aura Skin Care</span>
              <span className="text-[10px] text-rose-300 font-medium tracking-wide">Enter Boutique &rsaquo;</span>
            </div>
          </div>
        </div>
      </div>

      {/* মেঝের ইন্টারেক্টিভ গোল্ডেন ক্রেস্ট ও ওয়েপয়েন্ট অ্যারো (Center Floor) */}
      <div className="absolute left-1/2 bottom-[16%] -translate-x-1/2 flex flex-col items-center pointer-events-auto z-20 cursor-pointer group">
        <button
          onClick={scrollToCatalog}
          onMouseEnter={() => setActiveSector("atrium")}
          className="flex flex-col items-center text-center focus:outline-none"
          title="Proceed into Grand Atrium"
        >
          {/* পালসিং গোল্ডেন অ্যারো */}
          <div className="w-10 h-10 flex items-center justify-center rounded-full bg-black/60 backdrop-blur-md border border-gold-400/60 shadow-gold group-hover:border-gold-300 group-hover:scale-110 transition-all duration-300">
            <svg
              viewBox="0 0 24 24"
              className="w-5 h-5 text-gold-300 group-hover:text-gold-200 transition-colors animate-bounce"
              fill="currentColor"
            >
              <polygon points="12,3 22,21 12,16 2,21" />
            </svg>
          </div>
          <span className="mt-1.5 px-3 py-0.5 rounded-full bg-black/70 backdrop-blur-md border border-gold-500/30 text-[10px] font-bold text-gold-200 uppercase tracking-widest group-hover:text-white transition-colors">
            Enter Grand Atrium
          </span>
        </button>
      </div>

      {/* ========================================================================= */}
      {/* বটম-লেফট HUD: সম্পূর্ণ ইন্টারেক্টিভ সার্কুলার মিনিম্যাপ / রাডার */}
      {/* ========================================================================= */}
      <div className="absolute left-4 sm:left-8 bottom-6 z-30">
        <div className="flex flex-col items-start gap-1.5">
          <div
            className="relative group p-1.5 rounded-full bg-[#0a0d14]/90 backdrop-blur-2xl border-2 border-gold-400/60 shadow-[0_0_25px_rgba(212,175,55,0.4)] transition-all duration-300"
          >
            {/* সার্কুলার রাডার স্ক্রিন */}
            <div className="relative w-28 h-28 sm:w-32 sm:h-32 rounded-full bg-[#080b10] border border-gold-400/30 overflow-hidden flex items-center justify-center">
              {/* রাডার কনসেন্ট্রিক রিং */}
              <div className="absolute inset-2 rounded-full border border-gold-400/15" />
              <div className="absolute inset-5 rounded-full border border-gold-400/15" />
              <div className="absolute inset-8 rounded-full border border-dashed border-gold-400/20 animate-[spin_40s_linear_infinite]" />

              {/* রাডার ক্রসহেয়ার অ্যাক্সিস */}
              <div className="absolute inset-x-0 top-1/2 h-px bg-gold-400/20" />
              <div className="absolute inset-y-0 left-1/2 w-px bg-gold-400/20" />

              {/* কার্ডিনাল ডিরেকশন লেবেল */}
              <span className="absolute top-1 text-[8px] font-extrabold text-gold-300 tracking-wider">N</span>
              <span className="absolute bottom-1 text-[8px] font-bold text-zinc-600">S</span>
              <span className="absolute right-1.5 text-[8px] font-bold text-zinc-600">E</span>
              <span className="absolute left-1.5 text-[8px] font-bold text-zinc-600">W</span>

              {/* রাডার গ্রিড ডটস */}
              <div className="absolute inset-0 opacity-20 bg-[radial-gradient(#d4af37_1px,transparent_1px)] [background-size:12px_12px]" />

              {/* সুইপিং রাডার স্ক্যান বিম */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-transparent via-gold-500/15 to-transparent animate-[spin_5s_linear_infinite] pointer-events-none" />

              {/* ইন্টারেক্টিভ রাডার ব্লিপস (Clickable Sectors on Map) */}
              {/* 1. Best Gadget (West) */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleSectorClick("gadget");
                }}
                className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full flex items-center justify-center transition-all ${
                  activeSector === "gadget"
                    ? "bg-cyan-400 text-black scale-125 shadow-[0_0_12px_#22d3ee]"
                    : "bg-cyan-500/40 text-cyan-200 hover:scale-110"
                }`}
                title="West Wing: Best Gadget"
              >
                <span className="text-[7px] font-black">G</span>
              </button>

              {/* 2. Aura Skin Care (East) */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleSectorClick("skincare");
                }}
                className={`absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full flex items-center justify-center transition-all ${
                  activeSector === "skincare"
                    ? "bg-rose-400 text-black scale-125 shadow-[0_0_12px_#fb7185]"
                    : "bg-rose-500/40 text-rose-200 hover:scale-110"
                }`}
                title="East Wing: Aura Skin Care"
              >
                <span className="text-[7px] font-black">S</span>
              </button>

              {/* 3. Grand Atrium (Center) */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleSectorClick("atrium");
                }}
                className={`absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-5 h-5 rounded-full flex items-center justify-center transition-all ${
                  activeSector === "atrium"
                    ? "bg-gold-400 text-black shadow-[0_0_12px_rgba(212,175,55,0.8)]"
                    : "bg-gold-500/30 text-gold-200"
                }`}
                title="Center: Grand Atrium"
              >
                <span className="text-[8px] font-black">A</span>
              </button>

              {/* কম্পাস পয়েন্টার নিডেল */}
              <div
                className="absolute inset-0 flex items-center justify-center pointer-events-none transition-transform duration-500 ease-out"
                style={{ transform: `rotate(${needleRotation}deg)` }}
              >
                <Navigation className="w-6 h-6 text-gold-400 fill-gold-400 drop-shadow-[0_0_6px_rgba(212,175,55,0.8)] transform -translate-y-2" />
              </div>
            </div>

            {/* ফুল ম্যাপ এক্সপ্যান্ড বাটন */}
            <button
              onClick={() => setIsMapExpanded(true)}
              className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-black/90 border border-gold-400/50 flex items-center justify-center text-gold-300 hover:bg-gold-500/30 transition-colors shadow-lg"
              title="Open Directory Floor Plan"
            >
              <Layers className="w-3 h-3" />
            </button>
          </div>

          {/* লাইভ HUD রিডআউট ব্যাজ */}
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-black/85 backdrop-blur-md border border-gold-500/30 shadow-lg">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[10px] font-bold tracking-wider text-gold-300 uppercase">
              {activeSector === "gadget"
                ? "Sector W: Best Gadget"
                : activeSector === "skincare"
                ? "Sector E: Aura Skin Care"
                : "Grand Atrium • Floor 1"}
            </span>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* বটম-রাইট HUD: "Explore the Mall" ডায়মন্ড অ্যাকশন বাটন */}
      {/* ========================================================================= */}
      <div className="absolute right-4 sm:right-8 bottom-6 z-30">
        <button
          onClick={scrollToCatalog}
          className="flex items-center gap-2.5 px-6 py-3 rounded-full bg-gradient-to-r from-[#1b150b] via-[#2d2211] to-[#1b150b] border border-gold-400/80 text-[#ffe89e] text-xs sm:text-sm font-bold tracking-wider shadow-[0_0_30px_rgba(212,175,55,0.4)] hover:shadow-[0_0_40px_rgba(212,175,55,0.7)] hover:border-gold-300 hover:scale-105 active:scale-95 transition-all duration-300 group"
        >
          {/* ডায়মন্ড আইকন */}
          <div className="w-5 h-5 rounded-full bg-gold-400/20 flex items-center justify-center text-gold-300 group-hover:rotate-45 transition-transform duration-300">
            <Sparkles className="w-3.5 h-3.5 fill-gold-400 text-gold-300" />
          </div>

          <span className="font-serif uppercase tracking-widest text-gold-gradient">
            Explore the Mall
          </span>

          <ChevronRight className="w-4 h-4 text-gold-400 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>

      {/* ========================================================================= */}
      {/* ইন্টারেক্টিভ বুটিক স্পটলাইট মোডাল (যখন ইউজার কোনো স্টোরে ক্লিক করে) */}
      {/* ========================================================================= */}
      {spotlightStore && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
          <div className="relative w-full max-w-2xl rounded-3xl bg-[#0e1219] border border-gold-400/50 shadow-[0_0_50px_rgba(212,175,55,0.3)] overflow-hidden flex flex-col max-h-[90vh]">
            {/* মোডাল হেডার */}
            <div className="relative p-6 pb-4 border-b border-gold-500/20 bg-gradient-to-r from-[#171c26] to-[#0e1219] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-gold-500/20 border border-gold-400/40 flex items-center justify-center text-gold-300">
                  <Store className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-serif text-xl font-bold text-gold-gradient">
                    {spotlightStore.name}
                  </h3>
                  <p className="text-xs text-zinc-400">
                    {spotlightStore.name.toLowerCase().includes("gadget")
                      ? "Smart Tech. Better Life. • Official Flagship Store"
                      : "Glow Naturally • Official Luxury Cosmetics Boutique"}
                  </p>
                </div>
              </div>

              <button
                onClick={() => setSpotlightStore(null)}
                className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-zinc-300 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* মোডাল কন্টেন্ট: স্টোর লাইভ প্রোডাক্টস */}
            <div className="p-6 overflow-y-auto space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-gold-300">
                  Featured Boutique Products
                </span>
                <span className="text-xs text-zinc-400">
                  {spotlightProducts.length} items available
                </span>
              </div>

              {spotlightProducts.length === 0 ? (
                <div className="py-12 text-center text-zinc-400 text-xs">
                  Loading boutique inventory...
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {spotlightProducts.map((p) => {
                    const price = prices[p.id] ?? 0;
                    const primaryImage =
                      p.images?.find((img) => img.is_primary)?.image_url ??
                      p.images?.[0]?.image_url ??
                      "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=300&h=300&fit=crop";

                    return (
                      <div
                        key={p.id}
                        className="group relative rounded-2xl border border-white/10 bg-[#141923] p-3 flex gap-3 items-center hover:border-gold-400/40 transition-colors"
                      >
                        <div className="relative w-16 h-16 rounded-xl overflow-hidden bg-black flex-shrink-0">
                          <Image
                            src={primaryImage}
                            alt={p.name}
                            fill
                            className="object-cover group-hover:scale-105 transition-transform"
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-xs text-zinc-100 truncate group-hover:text-gold-300">
                            {p.name}
                          </h4>
                          <p className="font-serif text-sm font-bold text-gold-gradient mt-0.5">
                            ৳{price.toFixed(2)}
                          </p>
                          <div className="flex items-center gap-2 mt-2">
                            <Link
                              href={`/shop/${p.id}`}
                              className="px-2.5 py-1 rounded-md bg-white/10 hover:bg-white/20 text-[10px] font-semibold text-zinc-200 transition-colors"
                            >
                              Details
                            </Link>
                            <button
                              onClick={() => handleQuickAddToCart(p)}
                              disabled={addingId === p.id}
                              className="px-2.5 py-1 rounded-md bg-gold-gradient text-black text-[10px] font-bold hover:opacity-90 transition-opacity flex items-center gap-1 shadow-sm"
                            >
                              {addingId === p.id ? (
                                <span className="animate-spin text-[10px]">&#9696;</span>
                              ) : (
                                <ShoppingCart className="w-3 h-3" />
                              )}
                              <span>Add</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* মোডাল ফুটার */}
            <div className="p-4 border-t border-gold-500/20 bg-[#0b0e14] flex items-center justify-between">
              <button
                onClick={() => {
                  onSelectStore(spotlightStore.id);
                  setSpotlightStore(null);
                  scrollToCatalog();
                }}
                className="w-full py-2.5 rounded-xl bg-gold-gradient text-black font-bold text-xs uppercase tracking-wider shadow-gold hover:opacity-95 transition-all text-center"
              >
                View Full {spotlightStore.name} Boutique Collection &rsaquo;
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* ফুল ফ্লোর প্ল্যান / ডিরেক্টরি ম্যাপ মোডাল */}
      {/* ========================================================================= */}
      {isMapExpanded && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md">
          <div className="relative w-full max-w-xl rounded-3xl bg-[#0e1219] border border-gold-400/50 p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-gold-500/20 mb-4">
              <div className="flex items-center gap-2">
                <Compass className="w-5 h-5 text-gold-400" />
                <h3 className="font-serif text-lg font-bold text-gold-gradient">
                  Aura Bell Grand Mall Directory
                </h3>
              </div>
              <button
                onClick={() => setIsMapExpanded(false)}
                className="p-1 rounded-full text-zinc-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              <div
                onClick={() => {
                  setIsMapExpanded(false);
                  if (bestGadgetStore) setSpotlightStore(bestGadgetStore);
                }}
                className="p-4 rounded-2xl bg-cyan-950/30 border border-cyan-400/30 hover:border-cyan-400 cursor-pointer transition-all flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-cyan-500/20 flex items-center justify-center text-cyan-300">
                    <Cpu className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-cyan-200">Sector West: Best Gadget</h4>
                    <p className="text-xs text-zinc-400">Laptops, Audio, Smart Devices • Level 1</p>
                  </div>
                </div>
                <span className="text-xs font-bold text-cyan-300">Enter &rsaquo;</span>
              </div>

              <div
                onClick={() => {
                  setIsMapExpanded(false);
                  if (auraSkinCareStore) setSpotlightStore(auraSkinCareStore);
                }}
                className="p-4 rounded-2xl bg-rose-950/30 border border-rose-400/30 hover:border-rose-400 cursor-pointer transition-all flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-rose-500/20 flex items-center justify-center text-rose-300">
                    <Flower2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-rose-200">Sector East: Aura Skin Care</h4>
                    <p className="text-xs text-zinc-400">Natural Glow, Serums, Organic Creams • Level 1</p>
                  </div>
                </div>
                <span className="text-xs font-bold text-rose-300">Enter &rsaquo;</span>
              </div>

              <div
                onClick={() => {
                  setIsMapExpanded(false);
                  onSelectStore(null);
                  scrollToCatalog();
                }}
                className="p-4 rounded-2xl bg-amber-950/30 border border-gold-400/30 hover:border-gold-400 cursor-pointer transition-all flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-gold-500/20 flex items-center justify-center text-gold-300">
                    <Store className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-gold-200">Central Atrium: All Collections</h4>
                    <p className="text-xs text-zinc-400">Grand Marketplace Directory</p>
                  </div>
                </div>
                <span className="text-xs font-bold text-gold-300">Explore &rsaquo;</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
