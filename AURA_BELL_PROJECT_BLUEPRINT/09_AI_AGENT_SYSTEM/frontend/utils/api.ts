// utils/api.ts
// Centralized API client for Aura Bell frontend.
// Uses fetch with bearer token from sessionStorage.

export interface ApiResponse<T> {
  data: T;
  error?: string;
}

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

function getAuthHeader(): HeadersInit {
  const token = typeof window !== "undefined" ? sessionStorage.getItem("access_token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse<T>(resp: Response): Promise<ApiResponse<T>> {
  const text = await resp.text();
  try {
    const json = JSON.parse(text);
    if (!resp.ok) {
      return { data: json as T, error: json?.detail || resp.statusText };
    }
    return { data: json as T };
  } catch {
    // not json
    if (!resp.ok) {
      return { data: null as any, error: resp.statusText };
    }
    return { data: null as any };
  }
}

// Cart APIs
export interface CartItemRead {
  variant_id: string;
  quantity: number;
  store_id: string;
  product_name: string;
  variant_name: string;
  price: number;
  image_url?: string;
  available: boolean;
}

export interface CartRead {
  items: CartItemRead[];
}

export async function fetchCart(userId: string, sessionId: string): Promise<ApiResponse<CartRead>> {
  const url = `${BASE_URL}/api/v1/cart?user_id=${encodeURIComponent(userId)}&session_id=${encodeURIComponent(sessionId)}`;
  const resp = await fetch(url, { headers: getAuthHeader() });
  return handleResponse<CartRead>(resp);
}

export async function addCartItem(item: { variant_id: string; quantity: number }): Promise<ApiResponse<any>> {
  const url = `${BASE_URL}/api/v1/cart/items`;
  const resp = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify(item),
  });
  return handleResponse<any>(resp);
}

export async function updateCartItem(variantId: string, quantity: number): Promise<ApiResponse<any>> {
  const url = `${BASE_URL}/api/v1/cart/items/${encodeURIComponent(variantId)}`;
  const resp = await fetch(url, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify({ quantity }),
  });
  return handleResponse<any>(resp);
}

export async function removeCartItem(variantId: string): Promise<ApiResponse<any>> {
  const url = `${BASE_URL}/api/v1/cart/items/${encodeURIComponent(variantId)}`;
  const resp = await fetch(url, {
    method: "DELETE",
    headers: getAuthHeader(),
  });
  return handleResponse<any>(resp);
}

// Checkout preview
export interface CheckoutPreviewItem {
  store_id: string;
  store_name: string;
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

export async function getCheckoutPreview(payload: any): Promise<ApiResponse<CheckoutPreview>> {
  const url = `${BASE_URL}/api/v1/cart/preview`;
  const resp = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<CheckoutPreview>(resp);
}

// Order APIs
export interface OrderResponse {
  order_id: string;
  status: string;
}

export async function checkoutOrder(orderPayload: any): Promise<ApiResponse<OrderResponse>> {
  const url = `${BASE_URL}/api/v1/orders/checkout`;
  const resp = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify(orderPayload),
  });
  return handleResponse<OrderResponse>(resp);
}

export async function verifyCodOtp(orderId: string, otp: string): Promise<ApiResponse<any>> {
  const url = `${BASE_URL}/api/v1/orders/${encodeURIComponent(orderId)}/verify-cod`;
  const resp = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify({ otp }),
  });
  return handleResponse<any>(resp);
}
