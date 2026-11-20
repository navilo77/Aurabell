import React from "react";
import { CheckoutPreview } from "../utils/api";
import { Button } from "@/ui/design-system"; // Adjust import if needed

interface Props {
  preview: CheckoutPreview | null;
  onProceed: () => void;
}

export const CartSummary: React.FC<Props> = ({ preview, onProceed }) => {
  if (!preview) return null;
  const { subtotal, discount, delivery_fee, grand_total, items } = preview;
  // compute per-store subtotals
  const storeMap: Record<string, number> = {};
  items.forEach((it) => {
    storeMap[it.store_name ?? it.store_id] = (storeMap[it.store_name ?? it.store_id] ?? 0) + it.line_total;
  });
  return (
    <div className="p-4 border rounded mt-4">
      <h2 className="text-lg font-semibold mb-2">সামগ্রিক সারাংশ (Cart Summary)</h2>
      <ul className="mb-2">
        {Object.entries(storeMap).map(([store, amt]) => (
          <li key={store} className="flex justify-between">
            <span>{store}</span>
            <span>&#8377;{amt.toFixed(2)}</span>
          </li>
        ))}
      </ul>
      <div className="flex justify-between"><span>Subtotal</span><span>&#8377;{subtotal.toFixed(2)}</span></div>
      <div className="flex justify-between"><span>Discount</span><span>-&#8377;{discount.toFixed(2)}</span></div>
      <div className="flex justify-between"><span>Delivery Fee</span><span>&#8377;{delivery_fee.toFixed(2)}</span></div>
      <hr className="my-2" />
      <div className="flex justify-between font-bold"><span>Grand Total</span><span>&#8377;{grand_total.toFixed(2)}</span></div>
      <Button onClick={onProceed} className="mt-4 w-full" disabled={items.some(i=>!i.available)}>
        Proceed to Checkout (চালিয়ে যান)
      </Button>
    </div>
  );
};
