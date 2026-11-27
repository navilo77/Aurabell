"use client";

import Image from "next/image";
import {
  Sparkles,
  Cpu,
  Flower2,
  ShieldCheck,
  Truck,
  Layers,
  ArrowRight,
  ChevronDown,
} from "lucide-react";
import { StoreRead } from "@/lib/types";

interface Hero2DProps {
  stores: StoreRead[];
  selectedStoreId: string | null;
  onSelectStore: (storeId: string | null) => void;
}

export function Hero2D({
  stores,
  selectedStoreId,
  onSelectStore,
}: Hero2DProps) {
  const bestGadgetStore = stores.find((s) =>
    s.name.toLowerCase().includes("gadget")
  );
  const auraSkinCareStore = stores.find((s) =>
    s.name.toLowerCase().includes("skin") || s.name.toLowerCase().includes("aura")
  );

  const handleScrollToCatalog = () => {
    const el = document.getElementById("marketplace-catalog");
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <section className="relative w-full overflow-hidden select-none">
      {/* Cinematic Grand Palace Luxury Mall Backdrop */}
      <div className="relative w-full h-[70vh] min-h-[520px] max-h-[720px] flex items-center justify-center">
        <Image
          src="/images/virtual-mall.jpg"
          alt="Aura Bell Grand Luxury Flagship Mall"
          fill
          priority
          className="object-cover object-center"
        />

        {/* Ambient Warm Golden & Dark Vignette Gradient Overlays */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#090b0e] via-[#090b0e]/40 to-black/60 pointer-events-none" />
        <div className="absolute inset-0 bg-gradient-to-r from-black/60 via-transparent to-black/60 pointer-events-none" />
        {/* Radial Vignette — prevents hero text blending into background columns */}
        <div className="absolute inset-0 hero-vignette pointer-events-none" />

        {/* Center Grand Brand Showcase */}
        <div className="relative z-10 text-center max-w-4xl mx-auto px-4 pt-16 flex flex-col items-center">
          {/* Official Seal Pill */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-black/60 backdrop-blur-xl border border-gold-400/40 text-gold-300 text-xs font-bold mb-4 shadow-gold">
            <Sparkles className="w-3.5 h-3.5 text-gold-400" />
            <span>Official Dual-Flagship Marketplace</span>
          </div>

          {/* Grand Brand Logo */}
          <h1 className="font-serif text-4xl sm:text-6xl md:text-7xl font-black tracking-wider text-white drop-shadow-[0_4px_16px_rgba(0,0,0,0.9)]">
            AURA <span className="text-gold-gradient">BELL</span>
          </h1>
          <p className="font-serif text-xs sm:text-sm text-[#f5df88] tracking-[0.3em] uppercase font-bold mt-2 drop-shadow-md">
            Shop Beyond Limits
          </p>

          <p className="mt-4 text-xs sm:text-sm text-zinc-200 max-w-lg mx-auto leading-relaxed drop-shadow-md">
            Experience authentic smart technology and luxury skincare from our two official flagship boutiques in a single shared order.
          </p>

          {/* Two Floating Glass Flagship Boutique Portals */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-2xl mt-8">
            {/* Best Gadget Flagship Portal */}
            <div
              onClick={() => {
                if (bestGadgetStore) onSelectStore(bestGadgetStore.id);
                handleScrollToCatalog();
              }}
              className={`group p-4 sm:p-5 rounded-2xl cursor-pointer transition-all duration-300 backdrop-blur-xl flex items-center justify-between border ${
                selectedStoreId === bestGadgetStore?.id
                  ? "bg-[#0c1a2e]/90 border-cyan-400 shadow-[0_0_25px_rgba(34,211,238,0.4)] scale-102"
                  : "bg-[#0a121c]/80 border-cyan-500/30 hover:border-cyan-400 hover:bg-[#0c1a2e]/90 hover:shadow-[0_0_20px_rgba(34,211,238,0.25)]"
              }`}
            >
              <div className="flex items-center gap-3.5 text-left">
                <div className="w-11 h-11 rounded-xl bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300 group-hover:scale-110 transition-transform">
                  <Cpu className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                  <h3 className="font-serif text-sm sm:text-base font-bold text-white group-hover:text-cyan-300 transition-colors">
                    Best Gadget
                  </h3>
                  <p className="text-[11px] text-cyan-400 font-mono">
                    Smart Tech. Better Life.
                  </p>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-cyan-400 group-hover:translate-x-1 transition-transform" />
            </div>

            {/* Aura Skin Care Flagship Portal */}
            <div
              onClick={() => {
                if (auraSkinCareStore) onSelectStore(auraSkinCareStore.id);
                handleScrollToCatalog();
              }}
              className={`group p-4 sm:p-5 rounded-2xl cursor-pointer transition-all duration-300 backdrop-blur-xl flex items-center justify-between border ${
                selectedStoreId === auraSkinCareStore?.id
                  ? "bg-[#25101a]/90 border-rose-400 shadow-[0_0_25px_rgba(251,113,133,0.4)] scale-102"
                  : "bg-[#180a11]/80 border-rose-500/30 hover:border-rose-400 hover:bg-[#25101a]/90 hover:shadow-[0_0_20px_rgba(251,113,133,0.25)]"
              }`}
            >
              <div className="flex items-center gap-3.5 text-left">
                <div className="w-11 h-11 rounded-xl bg-rose-500/20 border border-rose-400/40 flex items-center justify-center text-rose-300 group-hover:scale-110 transition-transform">
                  <Flower2 className="w-5 h-5 text-rose-300" />
                </div>
                <div>
                  <h3 className="font-serif text-sm sm:text-base font-bold text-white group-hover:text-rose-300 transition-colors">
                    Aura Skin Care
                  </h3>
                  <p className="text-[11px] text-rose-300 font-mono">
                    Glow Naturally.
                  </p>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-rose-400 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Explore Collections Button */}
          <button
            onClick={handleScrollToCatalog}
            className="mt-8 flex items-center gap-2 px-6 py-2.5 rounded-full bg-gold-gradient text-black font-extrabold text-xs uppercase tracking-wider shadow-gold hover:opacity-95 transition-all group"
          >
            <span>Explore Collections</span>
            <ChevronDown className="w-4 h-4 group-hover:translate-y-0.5 transition-transform" />
          </button>
        </div>
      </div>

      {/* Trust Guarantee Strip — compact icon-centric bar */}
      <div className="bg-[#0a0c11] border-y border-gold-500/10 py-2.5 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-center sm:justify-between gap-2 sm:gap-0">
          <div className="flex items-center gap-2 justify-center">
            <ShieldCheck className="w-4 h-4 text-gold-400 flex-shrink-0" />
            <p className="text-[11px] font-semibold text-zinc-300">100% Genuine Guarantee</p>
          </div>
          <div className="hidden sm:block w-px h-4 bg-white/10" />
          <div className="flex items-center gap-2 justify-center">
            <Layers className="w-4 h-4 text-gold-400 flex-shrink-0" />
            <p className="text-[11px] font-semibold text-zinc-300">Shared Multi-Store Cart</p>
          </div>
          <div className="hidden sm:block w-px h-4 bg-white/10" />
          <div className="flex items-center gap-2 justify-center">
            <Truck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <p className="text-[11px] font-semibold text-zinc-300">Cash on Delivery (COD)</p>
          </div>
        </div>
      </div>
    </section>
  );
}
