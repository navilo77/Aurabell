import React from "react";
import { CartItemRead } from "../utils/api";
import { Button, Input } from "@/ui/design-system"; // Adjust import path as per project

interface Props {
  item: CartItemRead;
  onQuantityChange: (variantId: string, newQty: number) => void;
  onRemove: (variantId: string) => void;
}

export const CartItem: React.FC<Props> = ({ item, onQuantityChange, onRemove }) => {
  const handleDecrement = () => {
    if (item.quantity > 1) {
      onQuantityChange(item.variant_id, item.quantity - 1);
    }
  };
  const handleIncrement = () => {
    onQuantityChange(item.variant_id, item.quantity + 1);
  };

  return (
    <div className="flex items-center justify-between p-2 border-b">
      <img src={item.image_url ?? "/placeholder.png"} alt={item.product_name} className="w-16 h-16 object-cover" />
      <div className="flex-1 ml-4">
        <div className="font-medium">{item.product_name}</div>
        <div className="text-sm text-gray-500">{item.variant_name} - {item.store_id}</div>
        <div className="text-sm">&#8377;{item.price.toFixed(2)}</div>
      </div>
      <div className="flex items-center space-x-2">
        <Button onClick={handleDecrement} disabled={item.quantity <= 1}>-</Button>
        <Input value={item.quantity.toString()} readOnly className="w-12 text-center" />
        <Button onClick={handleIncrement}>+</Button>
      </div>
      <div className="ml-4 font-medium">&#8377;{(item.price * item.quantity).toFixed(2)}</div>
      <Button onClick={() => onRemove(item.variant_id)} variant="danger" className="ml-2">✕</Button>
    </div>
  );
};
