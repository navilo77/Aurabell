"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { BrandShopConfig, StoreTheme, getBrandShopConfigs } from "@/lib/stores";
import { Sparkles, ArrowRight, Store as StoreIcon, Cpu, Flower2 } from "lucide-react";
import { StoreRead } from "@/lib/types";

const THEME_STYLES: Record<
  StoreTheme,
  {
    border: string;
    text: string;
    icon: string;
    gradient: string;
    glow: string;
    iconBg: string;
  }
> = {
  gadget: {
    border: "border-cyan-500/30 hover:border-cyan-400",
    text: "text-cyan-300",
    icon: "text-cyan-400",
    gradient: "from-[#0c1a2e] to-[#0a121c]",
    glow: "hover:shadow-[0_0_25px_rgba(34,211,238,0.3)]",
    iconBg: "bg-cyan-500/20 border-cyan-400/40",
  },
  skin: {
    border: "border-rose-500/30 hover:border-rose-400",
    text: "text-rose-300",
    icon: "text-rose-400",
    gradient: "from-[#25101a] to-[#180a11]",
    glow: "hover:shadow-[0_0_25px_rgba(251,113,133,0.3)]",
    iconBg: "bg-rose-500/20 border-rose-400/40",
  },
  generic: {
    border: "border-gold-500/30 hover:border-gold-400",
    text: "text-gold-300",
    icon: "text-gold-400",
    gradient: "from-[#1a150c] to-[#120e08]",
    glow: "hover:shadow-[0_0_25px_rgba(212,175,55,0.3)]",
    iconBg: "bg-gold-500/20 border-gold-400/40",
  },
};

export default function BrandShopsPage() {
  const [configs, setConfigs] = useState<BrandShopConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    apiFetch<StoreRead[]>("/stores")
      .then((storesData) => {
        if (!mounted) return;
        // Handle both array and paginated response
        const storesArray = Array.isArray(storesData) ? storesData : (storesData as { data?: StoreRead[] }).data ?? [];
        const activeStores = storesArray.filter((s) => s.status === "active") ?? [];
        setConfigs(getBrandShopConfigs(activeStores));
      })
      .catch((err) => {
        if (mounted) setError(err.message ?? "Failed to load brand shops");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-gold-400 border-t-transparent" />
          <p className="text-xs text-gold-300 uppercase tracking-widest font-mono">
            Loading Brand Shops...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-6 text-center max-w-md mx-auto">
          <p className="text-xs text-rose-300">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 text-sm text-gold-400 hover:underline"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (configs.length === 0) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="text-sm text-zinc-400">
          No active brand shops available right now.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {/* Hero header */}
      <div className="text-center max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-gold-500/15 border border-gold-400/30 text-gold-300 text-xs font-semibold mb-3">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Brand Directory</span>
        </div>
        <h1 className="font-serif text-3xl sm:text-4xl font-extrabold text-white">
          Brand <span className="text-gold-gradient">Shops</span>
        </h1>
        <p className="mt-2 text-sm text-zinc-400">
          The central marketplace entry point for every Aura Bell boutique — current
          and future.
        </p>
      </div>

      {/* Brand shop cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {configs.map((config) => {
          const theme = THEME_STYLES[config.theme];
          return (
            <Link
              key={config.id}
              href={`/${config.slug}`}
              className={`group relative flex flex-col rounded-2xl overflow-hidden border bg-gradient-to-br ${theme.gradient} ${theme.border} ${theme.glow} p-5 sm:p-6 transition-all duration-300`}
            >
              {/* Logo + category badge */}
              <div className="flex items-start justify-between gap-3">
                {config.logoUrl ? (
                  <div
                    className="h-14 w-14 rounded-xl border border-white/10 bg-white/5 bg-cover bg-center"
                    style={{ backgroundImage: `url(${config.logoUrl})` }}
                    role="img"
                    aria-label={`${config.name} logo`}
                  />
                ) : (
                  <div
                    className={`h-14 w-14 rounded-xl border flex items-center justify-center ${theme.iconBg}`}
                  >
                    {config.theme === "gadget" ? (
                      <Cpu className={`h-7 w-7 ${theme.icon}`} />
                    ) : config.theme === "skin" ? (
                      <Flower2 className={`h-7 w-7 ${theme.icon}`} />
                    ) : (
                      <StoreIcon className={`h-7 w-7 ${theme.icon}`} />
                    )}
                  </div>
                )}
                <span
                  className={`text-[10px] font-mono uppercase tracking-wider px-2 py-1 rounded-full border ${theme.iconBg} ${theme.text}`}
                >
                  {config.theme === "gadget"
                    ? "Tech"
                    : config.theme === "skin"
                      ? "Beauty"
                      : "Boutique"}
                </span>
              </div>

              {/* Name + tagline */}
              <h2 className="mt-4 font-serif text-lg font-bold text-white">
                {config.name}
              </h2>
              <p className={`text-[11px] font-mono ${theme.text}`}>
                {config.tagline}
              </p>

              {/* Description */}
              <p className="mt-2 text-xs text-zinc-400 leading-relaxed flex-1">
                {config.description}
              </p>

              {/* Visit Shop CTA */}
              <div className="mt-5">
                <span
                  className={`inline-flex items-center gap-1.5 px-3.5 py-2 rounded-full text-[10px] font-bold uppercase tracking-wider border ${theme.iconBg} ${theme.text}`}
                >
                  Visit Shop
                  <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-1" />
                </span>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Footer note */}
      <p className="text-center text-[11px] text-zinc-500 uppercase tracking-wider">
        {configs.length} active brand shop{configs.length !== 1 ? "s" : ""} on Aura
        Bell
      </p>
    </div>
  );
}