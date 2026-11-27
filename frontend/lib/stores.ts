"use client";

import { StoreRead } from "@/lib/types";

export interface StoreConfig {
  id: string;
  slug: "best-gadget" | "aura-skin-care";
  name: string;
  theme: "gadget" | "skin";
  accentColor: string;
  accentColorHover: string;
  accentColorLight: string;
  tagline: string;
  description: string;
}

const STORE_SLUG_MAP: Record<string, "best-gadget" | "aura-skin-care"> = {
  "best-gadget": "best-gadget",
  "aura-skin-care": "aura-skin-care",
};

export function getStoreSlugFromPath(pathname: string): "best-gadget" | "aura-skin-care" | null {
  const segments = pathname.split("/").filter(Boolean);
  if (segments[0] === "best-gadget") return "best-gadget";
  if (segments[0] === "aura-skin-care") return "aura-skin-care";
  return null;
}

export function getStoreConfig(stores: StoreRead[], slug: "best-gadget" | "aura-skin-care"): StoreConfig | null {
  const store = stores.find((s) => s.slug === slug);
  if (!store) return null;

  const isGadget = slug === "best-gadget";

  return {
    id: store.id,
    slug,
    name: store.name,
    theme: isGadget ? "gadget" : "skin",
    accentColor: isGadget ? "#0284c7" : "#e11d48",
    accentColorHover: isGadget ? "#0ea5e9" : "#fda4af",
    accentColorLight: isGadget ? "rgba(2, 132, 199, 0.1)" : "rgba(225, 29, 72, 0.1)",
    tagline: isGadget ? "Smart Tech. Better Life." : "Glow Naturally.",
    description: isGadget
      ? "Official distributor warranty guaranteed on all smart technology."
      : "Dermatologist tested, pure ingredients for radiant skin.",
  };
}

export function getStoreConfigById(stores: StoreRead[], storeId: string): StoreConfig | null {
  const store = stores.find((s) => s.id === storeId);
  if (!store) return null;

  const isGadget = store.slug === "best-gadget" || store.name.toLowerCase().includes("gadget");

  return {
    id: store.id,
    slug: store.slug as "best-gadget" | "aura-skin-care",
    name: store.name,
    theme: isGadget ? "gadget" : "skin",
    accentColor: isGadget ? "#0284c7" : "#e11d48",
    accentColorHover: isGadget ? "#0ea5e9" : "#fda4af",
    accentColorLight: isGadget ? "rgba(2, 132, 199, 0.1)" : "rgba(225, 29, 72, 0.1)",
    tagline: isGadget ? "Smart Tech. Better Life." : "Glow Naturally.",
    description: isGadget
      ? "Official distributor warranty guaranteed on all smart technology."
      : "Dermatologist tested, pure ingredients for radiant skin.",
  };
}

export function getAllStoreConfigs(stores: StoreRead[]): StoreConfig[] {
  return stores
    .filter((s) => STORE_SLUG_MAP[s.slug])
    .map((store) => {
      const isGadget = store.slug === "best-gadget";
      return {
        id: store.id,
        slug: store.slug as "best-gadget" | "aura-skin-care",
        name: store.name,
        theme: isGadget ? "gadget" : "skin",
        accentColor: isGadget ? "#0284c7" : "#e11d48",
        accentColorHover: isGadget ? "#0ea5e9" : "#fda4af",
        accentColorLight: isGadget ? "rgba(2, 132, 199, 0.1)" : "rgba(225, 29, 72, 0.1)",
        tagline: isGadget ? "Smart Tech. Better Life." : "Glow Naturally.",
        description: isGadget
          ? "Official distributor warranty guaranteed on all smart technology."
          : "Dermatologist tested, pure ingredients for radiant skin.",
      };
    });
}

export const CANONICAL_STORE_SLUGS = ["best-gadget", "aura-skin-care"] as const;

// ─── Brand Shop Directory (scalable, registry-driven) ────────────────────────
// Source of truth is the `stores` table (fetched via /api/v1/stores). These
// helpers only add presentation metadata, so brand new stores automatically
// appear on /brand-shops without any navbar changes.

export type StoreTheme = "gadget" | "skin" | "generic";

export interface BrandShopConfig {
  id: string;
  slug: string;
  name: string;
  theme: StoreTheme;
  accentColor: string;
  accentColorHover: string;
  accentColorLight: string;
  tagline: string;
  description: string;
  logoUrl: string | null;
  primaryColor: string | null;
}

const BRAND_THEME_ACCENTS: Record<
  StoreTheme,
  { accentColor: string; accentColorHover: string; accentColorLight: string }
> = {
  gadget: {
    accentColor: "#0284c7",
    accentColorHover: "#0ea5e9",
    accentColorLight: "rgba(2, 132, 199, 0.1)",
  },
  skin: {
    accentColor: "#e11d48",
    accentColorHover: "#fda4af",
    accentColorLight: "rgba(225, 29, 72, 0.1)",
  },
  generic: {
    accentColor: "#d4af37",
    accentColorHover: "#ebdfad",
    accentColorLight: "rgba(212, 175, 55, 0.1)",
  },
};

const BRAND_TAGLINES: Record<string, string> = {
  "best-gadget": "Smart Tech. Better Life.",
  "aura-skin-care": "Glow Naturally.",
};

const BRAND_DESCRIPTIONS: Record<string, string> = {
  "best-gadget": "Smartphones, laptops, audio & accessories — official distributor warranty guaranteed.",
  "aura-skin-care": "Serums, creams, cleansers & treatments — dermatologist tested for radiant skin.",
};

function resolveStoreTheme(slug: string): StoreTheme {
  if (slug === "best-gadget") return "gadget";
  if (slug === "aura-skin-care") return "skin";
  return "generic";
}

/**
 * Build presentation configs for every active store so the /brand-shops
 * directory renders current and future brands from the store registry.
 */
export function getBrandShopConfigs(stores: StoreRead[]): BrandShopConfig[] {
  return stores
    .filter((store) => store.status === "active")
    .map((store) => {
      const theme = resolveStoreTheme(store.slug);
      const accents = BRAND_THEME_ACCENTS[theme];

      return {
        id: store.id,
        slug: store.slug,
        name: store.name,
        theme,
        ...accents,
        tagline: BRAND_TAGLINES[store.slug] ?? "Official Boutique",
        description:
          BRAND_DESCRIPTIONS[store.slug] ??
          store.description ??
          `Explore the official ${store.name} boutique on Aura Bell.`,
        logoUrl: store.logo_url,
        primaryColor: store.primary_color,
      };
    });
}