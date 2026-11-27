"use client";

import React from "react";

// চেকআউট প্রিভিউ ডেটার টাইপ
interface CheckoutPreviewItem {
  store_id: string;
  store_name?: string;
  variant_id: string;
  quantity: number;
  unit_price: number;
  line_total: number;
  available: boolean;
}

export interface CheckoutPreview {
  items: CheckoutPreviewItem[];
  subtotal: number;
  delivery_fee: number;
  discount: number;
  grand_total: number;
}

interface Props {
  preview: CheckoutPreview | null;
  onProceed: () => void;
}

// কার্ট সামারি — মোট দাম, ডেলিভারি ফি, ডিসকাউন্ট, গ্র্যান্ড টোটাল দেখায়
export function CartSummary({ preview, onProceed }: Props) {
  if (!preview) return null;

  const toNum = (v: unknown): number => (typeof v === "number" ? v : Number(v)) || 0;
  const subtotal = toNum(preview.subtotal);
  const discount = toNum(preview.discount);
  const delivery_fee = toNum(preview.delivery_fee);
  const grand_total = toNum(preview.grand_total);

  // প্রতি স্টোরের সাব‑টোটাল হিসাব
  const storeMap: Record<string, number> = {};
  preview.items.forEach((it) => {
    const storeName = it.store_name ?? it.store_id;
    const lineTotal = toNum(it.line_total);
    storeMap[storeName] = (storeMap[storeName] ?? 0) + lineTotal;
  });

  // কোনো আইটেম unavailable থাকলে চেকআউট ডিসেবল
  const hasUnavailable = preview.items.some((i) => !i.available);

  return (
    <div className="rounded-lg border border-border bg-card p-6 mt-6">
      <h2 className="text-lg font-semibold text-foreground mb-4">
        সামগ্রিক সারাংশ (Order Summary)
      </h2>

      {/* প্রতি স্টোরের সাব‑টোটাল */}
      <div className="space-y-1 mb-4">
        {Object.entries(storeMap).map(([store, amt]) => (
          <div key={store} className="flex justify-between text-sm">
            <span className="text-muted-foreground">{store}</span>
            <span className="text-foreground">৳{amt.toFixed(2)}</span>
          </div>
        ))}
      </div>

      <div className="border-t border-border pt-3 space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Subtotal</span>
          <span className="text-foreground">৳{subtotal.toFixed(2)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Discount</span>
          <span className="text-green-600">−৳{discount.toFixed(2)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Delivery Fee</span>
          <span className="text-foreground">৳{delivery_fee.toFixed(2)}</span>
        </div>
      </div>

      <div className="border-t border-border mt-3 pt-3">
        <div className="flex justify-between text-lg font-bold">
          <span className="text-foreground">Grand Total</span>
          <span className="text-primary">৳{grand_total.toFixed(2)}</span>
        </div>
      </div>

      {hasUnavailable && (
        <p className="text-xs text-destructive mt-2">
          কিছু পণ্য স্টকে নেই — চেকআউট করতে সেগুলো সরিয়ে ফেলুন।
        </p>
      )}

      <button
        onClick={onProceed}
        disabled={hasUnavailable}
        className="mt-4 w-full rounded-md bg-primary px-4 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        চেকআউটে যান (Proceed to Checkout)
      </button>
    </div>
  );
}
