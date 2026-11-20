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
