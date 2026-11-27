"use client";

import React from "react";
import Image from "next/image";

// কার্ট আইটেমের টাইপ — ব্যাকএন্ড থেকে আসা ডেটার ধরন
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

interface Props {
  item: CartItemData;
  onQuantityChange: (variantId: string, newQty: number) => void;
  onRemove: (variantId: string) => void;
}

// কার্টে একটি পণ্যের সারি — ছবি, নাম, দাম, পরিমাণ বাটন, মুছে ফেলার বাটন
export function CartItem({ item, onQuantityChange, onRemove }: Props) {
  const toNum = (v: unknown): number => (typeof v === "number" ? v : Number(v)) || 0;
  const price = toNum(item.price);
  const lineTotal = price * item.quantity;

  const handleDecrement = () => {
    if (item.quantity > 1) {
      onQuantityChange(item.variant_id, item.quantity - 1);
    }
  };
  const handleIncrement = () => {
    onQuantityChange(item.variant_id, item.quantity + 1);
  };

  return (
    <div className="flex items-center gap-4 p-4 border-b border-border">
      {/* পণ্যের ছবি */}
      <Image
        src={item.image_url ?? "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=80&h=80&fit=crop"}
        alt={item.product_name}
        width={64}
        height={64}
        className="w-16 h-16 rounded-md object-cover bg-muted"
      />

      {/* পণ্যের তথ্য */}
      <div className="flex-1 min-w-0">
        <h3 className="font-semibold text-foreground truncate">{item.product_name}</h3>
        <p className="text-sm text-muted-foreground">{item.variant_name}</p>
        <p className="text-xs text-muted-foreground">Store: {item.store_id}</p>
        {!item.available && (
          <span className="text-xs text-destructive font-medium">স্টকে নেই</span>
        )}
      </div>

      {/* দাম */}
      <div className="text-sm font-medium text-foreground whitespace-nowrap">
        ৳{price.toFixed(2)}
      </div>

      {/* পরিমাণ নিয়ন্ত্রণ */}
      <div className="flex items-center gap-1">
        <button
          onClick={handleDecrement}
          disabled={item.quantity <= 1}
          className="w-8 h-8 rounded-md border border-input bg-background text-foreground hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          −
        </button>
        <span className="w-8 text-center text-sm font-medium text-foreground">
          {item.quantity}
        </span>
        <button
          onClick={handleIncrement}
          className="w-8 h-8 rounded-md border border-input bg-background text-foreground hover:bg-accent transition-colors"
        >
          +
        </button>
      </div>

      {/* লাইন টোটাল */}
      <div className="font-semibold text-foreground whitespace-nowrap w-20 text-right">
        ৳{lineTotal.toFixed(2)}
      </div>

      {/* মুছে ফেলার বাটন */}
      <button
        onClick={() => onRemove(item.variant_id)}
        className="w-8 h-8 rounded-md text-destructive hover:bg-destructive/10 transition-colors flex items-center justify-center"
        aria-label="Remove item"
      >
        ✕
      </button>
    </div>
  );
}
