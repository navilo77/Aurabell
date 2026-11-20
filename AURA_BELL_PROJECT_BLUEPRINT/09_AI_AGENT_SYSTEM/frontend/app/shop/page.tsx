"use client";
import React, { useEffect, useState } from "react";
import { fetchCart, getCheckoutPreview, CheckoutPreview } from "../../utils/api";
import { CartItem } from "../components/CartItem";
import { CartSummary } from "../components/CartSummary";
import { CheckoutModal } from "../components/CheckoutModal";
import { Spinner } from "@/ui/design-system"; // assume exists

interface CartPageProps {}

export default function ShopPage(props: CartPageProps) {
  const [cart, setCart] = useState<{ items: any[] } | null>(null);
  const [preview, setPreview] = useState<CheckoutPreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  // In real app, obtain userId/sessionId from auth context or cookies
  const userId = "demo_user";
  const sessionId = "demo_session";

  const loadCart = async () => {
    const resp = await fetchCart(userId, sessionId);
    if (!resp.error && resp.data) {
      setCart(resp.data);
    }
  };

  const loadPreview = async () => {
    const payload = { user_id: userId, session_id: sessionId, cart_items: cart?.items ?? [] };
    const resp = await getCheckoutPreview(payload);
    if (!resp.error && resp.data) setPreview(resp.data);
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      await loadCart();
      setLoading(false);
    };
    fetchData();
  }, []);

  // Update preview whenever cart changes
  useEffect(() => {
    if (cart) {
      loadPreview();
    }
  }, [cart]);

  const handleQuantityChange = async (variantId: string, newQty: number) => {
    // call updateCartItem then refresh cart
    const { updateCartItem } = await import("../utils/api");
    const resp = await updateCartItem(variantId, newQty);
    if (!resp.error) await loadCart();
  };

  const handleRemove = async (variantId: string) => {
    const { removeCartItem } = await import("../utils/api");
    const resp = await removeCartItem(variantId);
    if (!resp.error) await loadCart();
  };

  const handleProceed = () => {
    setModalOpen(true);
  };

  const handleSuccess = (orderId: string) => {
    // redirect to order confirmation page
    window.location.href = `/orders/${orderId}`;
  };

  if (loading) return <Spinner />;

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Shopping Cart (কার্ট)</h1>
      {cart?.items?.map(item => (
        <CartItem
          key={item.variant_id}
          item={item}
          onQuantityChange={handleQuantityChange}
          onRemove={handleRemove}
        />
      ))}
      <CartSummary preview={preview} onProceed={handleProceed} />
      <CheckoutModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        preview={preview}
        onSuccess={handleSuccess}
      />
    </div>
  );
}
