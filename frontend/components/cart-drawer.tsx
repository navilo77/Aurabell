"use client";

import { useEffect, useState, useCallback } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  X,
  ShoppingCart,
  Trash2,
  Plus,
  Minus,
  ArrowRight,
  Sparkles,
  ShoppingBag,
  Loader2,
  ShieldCheck,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useToast } from "@/components/ui/toast";

interface CartItemData {
  variant_id: string;
  quantity: number;
  store_id: string;
  product_name: string;
  variant_name: string;
  price: number;
  image_url?: string;
  available: boolean;
}

interface CheckoutPreview {
  items: any[];
  subtotal: number;
  delivery_fee: number;
  discount: number;
  grand_total: number;
}

export function CartDrawer() {
  const { toast } = useToast();
  const [isOpen, setIsOpen] = useState(false);
  const [items, setItems] = useState<CartItemData[]>([]);
  const [preview, setPreview] = useState<CheckoutPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const loadCartData = useCallback(async () => {
    try {
      const data = await apiFetch<{ items: CartItemData[] }>("/cart");
      const currentItems = data.items ?? [];
      setItems(currentItems);

      if (currentItems.length > 0) {
        try {
          const prev = await apiFetch<CheckoutPreview>("/cart/preview", {
            method: "POST",
            body: JSON.stringify({}),
          });
          setPreview(prev);
        } catch {
          // Ignore preview fallback
        }
      } else {
        setPreview(null);
      }
    } catch {
      // Fallback
    }
  }, []);

  useEffect(() => {
    loadCartData();

    const handleOpen = () => {
      setIsOpen(true);
      loadCartData();
    };

    const handleUpdate = () => {
      loadCartData();
    };

    window.addEventListener("open-cart-drawer", handleOpen);
    window.addEventListener("cart-updated", handleUpdate);

    return () => {
      window.removeEventListener("open-cart-drawer", handleOpen);
      window.removeEventListener("cart-updated", handleUpdate);
    };
  }, [loadCartData]);

  const handleQuantity = async (variantId: string, currentQty: number, delta: number) => {
    const newQty = currentQty + delta;
    if (newQty <= 0) {
      await handleRemove(variantId);
      return;
    }

    setUpdatingId(variantId);
    try {
      await apiFetch(`/cart/items/${variantId}`, {
        method: "PATCH",
        body: JSON.stringify({ quantity: newQty }),
      });
      await loadCartData();
      window.dispatchEvent(new Event("cart-updated"));
    } catch (e: any) {
      toast({
        title: "Error",
        description: e.message || "Failed to update quantity.",
        variant: "destructive",
      });
    } finally {
      setUpdatingId(null);
    }
  };

  const handleRemove = async (variantId: string) => {
    setUpdatingId(variantId);
    try {
      await apiFetch(`/cart/items/${variantId}`, { method: "DELETE" });
      await loadCartData();
      window.dispatchEvent(new Event("cart-updated"));
      toast({
        title: "Item Removed",
        description: "The item has been removed from your cart.",
      });
    } catch (e: any) {
      toast({
        title: "Error",
        description: e.message || "Failed to remove item.",
        variant: "destructive",
      });
    } finally {
      setUpdatingId(null);
    }
  };

  if (!isOpen) return null;

  // Group items by store
  const storeGroups = items.reduce<Record<string, CartItemData[]>>((acc, item) => {
    const sId = item.store_id || "general";
    if (!acc[sId]) acc[sId] = [];
    acc[sId].push(item);
    return acc;
  }, {});

  const totalItemsCount = items.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <div className="fixed inset-0 z-[100] flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/80 backdrop-blur-md animate-in fade-in duration-300"
        onClick={() => setIsOpen(false)}
      />

      {/* Drawer Panel */}
      <aside className="relative w-full max-w-md bg-[#0c0e14] border-l border-gold-500/30 shadow-2xl flex flex-col h-full z-10 animate-in slide-in-from-right duration-300">
        {/* Header */}
        <div className="p-5 border-b border-white/10 flex items-center justify-between bg-gradient-to-r from-[#141822] to-[#0c0e14]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gold-500/20 border border-gold-400/40 flex items-center justify-center text-gold-400">
              <ShoppingCart className="w-4 h-4" />
            </div>
            <div>
              <h2 className="font-serif text-base font-bold text-white flex items-center gap-2">
                Your Shared Cart
                <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-rose-600 text-white">
                  {totalItemsCount}
                </span>
              </h2>
              <p className="text-[11px] text-zinc-400">Unified Multi-Store Checkout</p>
            </div>
          </div>

          <button
            onClick={() => setIsOpen(false)}
            className="w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-zinc-400 hover:text-white transition-colors"
            aria-label="Close cart drawer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="w-16 h-16 rounded-3xl bg-gold-500/10 border border-gold-400/20 flex items-center justify-center text-gold-300 mb-4">
                <ShoppingBag className="w-7 h-7" />
              </div>
              <h3 className="font-serif text-lg font-bold text-zinc-200">
                Your cart is empty
              </h3>
              <p className="text-xs text-zinc-400 max-w-xs mt-1">
                Explore our curated collections from Best Gadget and Aura Skin Care.
              </p>
              <button
                onClick={() => setIsOpen(false)}
                className="mt-6 px-6 py-2.5 rounded-full bg-gold-gradient text-black font-bold text-xs uppercase tracking-wider shadow-gold hover:opacity-90 transition-opacity"
              >
                Start Shopping
              </button>
            </div>
          ) : (
            Object.entries(storeGroups).map(([storeId, storeItems]) => {
              const isGadget =
                storeId.toLowerCase().includes("gadget") ||
                storeItems.some((i) => i.product_name.toLowerCase().includes("tech") || i.product_name.toLowerCase().includes("gadget"));
              const isSkin =
                storeId.toLowerCase().includes("skin") ||
                storeItems.some((i) => i.product_name.toLowerCase().includes("skin") || i.product_name.toLowerCase().includes("care"));

              const storeLabel = isGadget
                ? "Best Gadget Boutique"
                : isSkin
                ? "Aura Skin Care Boutique"
                : `Store: ${storeId.slice(0, 8)}...`;

              return (
                <div
                  key={storeId}
                  className={`rounded-2xl p-4 border transition-all ${
                    isGadget
                      ? "bg-cyan-950/20 border-cyan-500/30"
                      : isSkin
                      ? "bg-rose-950/20 border-rose-500/30"
                      : "bg-[#12161f] border-gold-500/20"
                  }`}
                >
                  {/* Store Badge Header */}
                  <div className="flex items-center justify-between pb-3 mb-3 border-b border-white/10">
                    <span
                      className={`text-xs font-bold flex items-center gap-1.5 ${
                        isGadget ? "text-cyan-300" : isSkin ? "text-rose-300" : "text-gold-300"
                      }`}
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      {storeLabel}
                    </span>
                    <span className="text-[10px] text-zinc-400 font-mono">
                      {storeItems.length} item{storeItems.length !== 1 ? "s" : ""}
                    </span>
                  </div>

                  {/* Items in Store */}
                  <div className="space-y-3">
                    {storeItems.map((item) => {
                      const isBusy = updatingId === item.variant_id;
                      return (
                        <div
                          key={item.variant_id}
                          className="flex gap-3 items-center bg-black/40 rounded-xl p-2.5 border border-white/5"
                        >
                          <div className="relative w-14 h-14 rounded-lg overflow-hidden bg-black flex-shrink-0">
                            <Image
                              src={
                                item.image_url ??
                                "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=100&h=100&fit=crop"
                              }
                              alt={item.product_name}
                              fill
                              className="object-cover"
                            />
                          </div>

                          <div className="flex-1 min-w-0">
                            <h4 className="font-semibold text-xs text-zinc-100 truncate">
                              {item.product_name}
                            </h4>
                            <p className="text-[10px] text-zinc-400 truncate">
                              {item.variant_name || "Standard Edition"}
                            </p>
                            <p className="font-serif text-xs font-bold text-gold-gradient mt-1">
                              ৳{item.price.toFixed(2)}
                            </p>
                          </div>

                          {/* Quantity Controls */}
                          <div className="flex items-center gap-1 bg-white/5 rounded-lg border border-white/10 p-0.5">
                            <button
                              onClick={() => handleQuantity(item.variant_id, item.quantity, -1)}
                              disabled={isBusy}
                              className="w-6 h-6 flex items-center justify-center rounded text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
                              aria-label="Decrease quantity"
                            >
                              <Minus className="w-3 h-3" />
                            </button>
                            <span className="w-5 text-center text-xs font-bold text-white">
                              {isBusy ? <Loader2 className="w-3 h-3 animate-spin mx-auto" /> : item.quantity}
                            </span>
                            <button
                              onClick={() => handleQuantity(item.variant_id, item.quantity, 1)}
                              disabled={isBusy}
                              className="w-6 h-6 flex items-center justify-center rounded text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
                              aria-label="Increase quantity"
                            >
                              <Plus className="w-3 h-3" />
                            </button>
                          </div>

                          {/* Delete Item */}
                          <button
                            onClick={() => handleRemove(item.variant_id)}
                            disabled={isBusy}
                            className="p-1.5 rounded-lg text-zinc-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                            aria-label="Remove item"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer Summary & Checkout */}
        {items.length > 0 && (
          <div className="p-5 border-t border-white/10 bg-[#090b0f] space-y-3">
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between text-zinc-400">
                <span>Subtotal</span>
                <span className="font-mono text-zinc-200">
                  ৳{(preview?.subtotal ?? items.reduce((s, i) => s + i.price * i.quantity, 0)).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-zinc-400">
                <span>Estimated Delivery</span>
                <span className="font-mono text-emerald-400">
                  {preview?.delivery_fee === 0 ? "Free in Dhaka" : `৳${(preview?.delivery_fee ?? 60).toFixed(2)}`}
                </span>
              </div>
              {preview?.discount ? (
                <div className="flex justify-between text-gold-300">
                  <span>Discount Applied</span>
                  <span className="font-mono">-৳{preview.discount.toFixed(2)}</span>
                </div>
              ) : null}
              <div className="flex justify-between text-sm font-bold text-white pt-2 border-t border-white/10">
                <span>Grand Total</span>
                <span className="font-serif text-base text-gold-gradient font-bold">
                  ৳{(preview?.grand_total ?? items.reduce((s, i) => s + i.price * i.quantity, 0)).toFixed(2)}
                </span>
              </div>
            </div>

            <Link
              href="/shop/cart"
              onClick={() => setIsOpen(false)}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-full bg-gold-gradient text-black font-extrabold text-xs uppercase tracking-wider shadow-gold hover:opacity-95 transition-opacity active:scale-98"
            >
              <span>Proceed to Checkout</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <div className="flex items-center justify-center gap-2 text-[10px] text-zinc-500 pt-1">
              <ShieldCheck className="w-3.5 h-3.5 text-gold-400" />
              <span>Cash on Delivery & Secure OTP Verification</span>
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}
