export type UserRole =
  | "customer"
  | "store_manager"
  | "owner"
  | "admin"
  | "super_admin";

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthUser {
  id: string;
  email: string;
  roles: UserRole[];
}

export interface UserProfileRead {
  id: string;
  email: string;
  full_name: string | null;
  phone: string | null;
  status: string;
  roles: UserRole[];
  store_ids: string[];
}

export interface DecodedToken {
  sub?: string;
  email?: string;
  role?: string;
  exp?: number;
  iat?: number;
  [key: string]: unknown;
}

export interface CategoryTreeNode {
  id: string;
  name: string;
  slug?: string;
  children?: CategoryTreeNode[];
}

export interface ImageRead {
  id: string;
  product_id: string;
  image_url: string;
  alt_text: string | null;
  sort_order: number;
  is_primary: boolean;
}

export interface VariantRead {
  id: string;
  product_id: string;
  sku: string;
  variant_name: string | null;
  attributes: Record<string, string>;
  barcode: string | null;
  is_active: boolean;
  created_at: string | null;
}

export interface ProductRead {
  id: string;
  store_id: string;
  category_id: string | null;
  name: string;
  slug: string;
  description: string | null;
  brand: string | null;
  product_type: string | null;
  status: string;
  is_featured: boolean;
  created_at: string | null;
  updated_at: string | null;
  variants: VariantRead[];
  images: ImageRead[];
  price?: number;
  compareAtPrice?: number;
}

export interface StoreRead {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  logo_url: string | null;
  primary_color: string | null;
  status: string;
  created_at: string | null;
  updated_at: string | null;
  policies: unknown[];
}

export interface OrderItemRead {
  id: string;
  product_name_snapshot: string;
  sku_snapshot: string;
  variant_snapshot: Record<string, unknown> | null;
  unit_price: number;
  quantity: number;
  discount_amount: number;
  line_total: number;
}

export interface OrderRead {
  id: string;
  order_number: string;
  user_id: string | null;
  subtotal: number;
  discount_total: number;
  delivery_total: number;
  grand_total: number;
  currency_code: string;
  order_status: string;
  created_at: string;
  delivery_address: {
    recipient_name: string;
    phone: string;
    address_line: string;
    area?: string | null;
    upazila?: string | null;
    district?: string | null;
    division?: string | null;
    postal_code?: string | null;
  } | null;
  store_orders: OrderRead[];
  order_items: OrderItemRead[];
}

export interface OrderTimelineEntry {
  old_status: string | null;
  new_status: string;
  changed_by: string | null;
  note: string | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// ─── Community / Chat (BE-06) ───────────────────────────────────────────────

export interface CommunityProfileRead {
  user_id: string;
  display_name: string;
  avatar_url: string | null;
  bio: string | null;
  member_since: string | null;
}

export interface CommunityProfileUpdate {
  display_name?: string;
  avatar_url?: string | null;
  bio?: string | null;
}

export interface ConversationRead {
  id: string;
  created_at: string;
  updated_at: string;
  other_user: CommunityProfileRead | null;
  last_message: string | null;
  unread_count: number;
}

export interface ConversationCreate {
  recipient_id: string;
}

export interface MessageRead {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface MessageCreate {
  content: string;
}

export interface ConversationMemberRead {
  user_id: string;
  last_read_at: string | null;
  joined_at: string;
}

// ─── Payments (BE-07) ────────────────────────────────────────────────────────

export interface PaymentInitiateRequest {
  order_id: string;
}

export interface PaymentInitiateResponse {
  payment_id: string;
  payment_url: string;
  transaction_id: string | null;
}

export interface PaymentRead {
  id: string;
  order_id: string;
  provider: string;
  provider_reference: string | null;
  payment_method: string;
  amount: number;
  currency_code: string;
  status: string;
  paid_at: string | null;
  created_at: string;
  updated_at: string | null;
}

export type PaymentStatus =
  | "pending"
  | "authorized"
  | "paid"
  | "failed"
  | "partially_refunded"
  | "refunded";

export interface PaymentVerifyResponse {
  payment_id: string;
  order_id: string;
  status: string;
  gateway_status: string;
  amount: string;
}
