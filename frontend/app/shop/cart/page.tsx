"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { CartItem } from "@/components/cart-item";
import { CartSummary, CheckoutPreview } from "@/components/cart-summary";
import { CheckoutModal } from "@/components/checkout-modal";
import { Header } from "@/components/header";

// কার্ট আইটেমের টাইপ
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

// কার্ট পেজ — /shop/cart রুটে রেন্ডার হবে
export default function CartPage() {
  const [cartItems, setCartItems] = useState<CartItemData[]>([]);
  const [preview, setPreview] = useState<CheckoutPreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  // কার্ট ডেটা লোড
  const loadCart = async () => {
    try {
      const data = await apiFetch<{ items: CartItemData[] }>("/cart");
      setCartItems(data.items ?? []);
    } catch (e: any) {
      setError(e.message);
    }
  };

  // চেকআউট প্রিভিউ লোড — সাবটোটাল, ডেলিভারি ফি, গ্র্যান্ড টোটাল
  const loadPreview = async () => {
    try {
      const data = await apiFetch<CheckoutPreview>("/cart/preview", {
        method: "POST",
        body: JSON.stringify({}),
      });
      setPreview(data);
    } catch {
      // প্রিভিউ ফেল হলে চুপচাপ থাকবে
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await loadCart();
      setLoading(false);
    };
    init();
  }, []);

  // কার্ট পরিবর্তন হলে প্রিভিউ রিফ্রেশ
  useEffect(() => {
    if (cartItems.length > 0) {
      loadPreview();
    } else {
      setPreview(null);
    }
  }, [cartItems]);

  // পরিমাণ পরিবর্তন
  const handleQuantityChange = async (variantId: string, newQty: number) => {
    try {
      await apiFetch(`/cart/items/${variantId}`, {
        method: "PATCH",
        body: JSON.stringify({ quantity: newQty }),
      });
      await loadCart();
    } catch (e: any) {
      setError(e.message);
    }
  };

  // আইটেম মুছে ফেলা
  const handleRemove = async (variantId: string) => {
    try {
      await apiFetch(`/cart/items/${variantId}`, { method: "DELETE" });
      await loadCart();
    } catch (e: any) {
      setError(e.message);
    }
  };

  // চেকআউট সফল হলে অর্ডার পেজে যাওয়া
  const handleSuccess = (orderId: string) => {
    window.location.href = `/orders/${orderId}`;
  };

  // লোডিং স্পিনার
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-muted-foreground">কার্ট লোড হচ্ছে...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header title="Shopping Cart" />

      <main className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-foreground mb-6">
          🛒 আপনার কার্ট (Shopping Cart)
        </h1>

        {error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 mb-4 text-destructive">
            {error}
          </div>
        )}

        {cartItems.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-xl text-muted-foreground mb-4">
              আপনার কার্ট খালি
            </p>
            <a
              href="/shop"
              className="inline-block rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              শপিং শুরু করুন
            </a>
          </div>
        ) : (
          <>
            {/* কার্ট আইটেম লিস্ট */}
            <div className="rounded-lg border border-border bg-card">
              {cartItems.map((item) => (
                <CartItem
                  key={item.variant_id}
                  item={item}
                  onQuantityChange={handleQuantityChange}
                  onRemove={handleRemove}
                />
              ))}
            </div>

            {/* সামারি ও চেকআউট বাটন */}
            <CartSummary
              preview={preview}
              onProceed={() => setModalOpen(true)}
            />
          </>
        )}

        {/* চেকআউট মোডাল */}
        <CheckoutModal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          onSuccess={handleSuccess}
        />
      </main>
    </div>
  );
}
