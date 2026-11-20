"""Seed dummy e-commerce data into local Supabase database for manual cart/pricing testing."""

import psycopg2
from uuid import uuid4

CONN = psycopg2.connect(
    host="127.0.0.1",
    port=54322,
    user="postgres",
    password="postgres",
    dbname="postgres",
)
cur = CONN.cursor()


def ensure_single(value, what):
    """Return single row value from SELECT, or raise if not found."""
    if value is None:
        raise ValueError(f"{what} not found")
    return value


# ── Store IDs ───────────────────────────────────────────────────────────
cur.execute("SELECT id FROM public.stores WHERE slug = 'best-gadget'")
best_gadget_id = ensure_single(cur.fetchone(), "best-gadget store")[0]

cur.execute("SELECT id FROM public.stores WHERE slug = 'aura-skin-care'")
aura_skin_care_id = ensure_single(cur.fetchone(), "aura-skin-care store")[0]

# ── Warehouses ──────────────────────────────────────────────────────────
# Best Gadget already has "Main Central Warehouse"
cur.execute("SELECT id FROM public.warehouses WHERE store_id = %s", [best_gadget_id])
best_gadget_warehouse_id = cur.fetchone()[0]

# Create warehouse for Aura Skin Care
aura_skin_care_warehouse_id = str(uuid4())
cur.execute(
    "INSERT INTO public.warehouses (id, store_id, name, location, is_active) "
    "VALUES (%s, %s, %s, %s, %s)",
    [aura_skin_care_warehouse_id, aura_skin_care_id, "Aura Skin Care Warehouse", "Dhaka, BD", True],
)

# ── Categories ──────────────────────────────────────────────────────────
# Smartphones already exists for Best Gadget
cur.execute("SELECT id FROM public.categories WHERE name = 'Smartphones' AND store_id = %s", [best_gadget_id])
smartphones_cat_id = cur.fetchone()[0]

# Laptops (Best Gadget)
laptops_cat_id = str(uuid4())
cur.execute(
    "INSERT INTO public.categories (id, store_id, name, slug, description, sort_order, is_active) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
    [laptops_cat_id, best_gadget_id, "Laptops", "laptops", "Laptops and notebooks", 0, True],
)

# Face Wash (Aura Skin Care)
face_wash_cat_id = str(uuid4())
cur.execute(
    "INSERT INTO public.categories (id, store_id, name, slug, description, sort_order, is_active) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
    [face_wash_cat_id, aura_skin_care_id, "Face Wash", "face-wash", "Facial cleansers", 0, True],
)

# ── Products ────────────────────────────────────────────────────────────
def insert_product(sql, params):
    cur.execute(sql, params)
    return cur.fetchone()[0]


iphone_15_id = insert_product(
    "INSERT INTO public.products (store_id, category_id, name, slug, description, brand, product_type, status, is_featured) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
    [
        best_gadget_id,
        smartphones_cat_id,
        "iPhone 15",
        "iphone-15",
        "Apple iPhone 15 128GB",
        "Apple",
        "phone",
        "active",
        True,
    ],
)

macbook_pro_id = insert_product(
    "INSERT INTO public.products (store_id, category_id, name, slug, description, brand, product_type, status, is_featured) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
    [
        best_gadget_id,
        laptops_cat_id,
        "MacBook Pro",
        "macbook-pro",
        "Apple MacBook Pro M3 14-inch",
        "Apple",
        "laptop",
        "active",
        True,
    ],
)

vitamin_c_serum_id = insert_product(
    "INSERT INTO public.products (store_id, category_id, name, slug, description, brand, product_type, status, is_featured) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
    [
        aura_skin_care_id,
        face_wash_cat_id,
        "Vitamin C Serum",
        "vitamin-c-serum",
        "Brightening Vitamin C Serum 30ml",
        "Aura Skin Care",
        "skincare",
        "active",
        True,
    ],
)

# ── Variants ────────────────────────────────────────────────────────────
def insert_variant(sql, params):
    cur.execute(sql, params)
    return cur.fetchone()[0]


iphone_variant_id = insert_variant(
    "INSERT INTO public.product_variants (product_id, sku, variant_name, attributes, barcode, is_active) "
    "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
    [iphone_15_id, "IPHONE-15-128GB", "128GB - Blue", '{"color":"blue","storage":"128GB"}', "1234567890128", True],
)

macbook_variant_id = insert_variant(
    "INSERT INTO public.product_variants (product_id, sku, variant_name, attributes, barcode, is_active) "
    "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
    [macbook_pro_id, "MACBOOK-M3-14", "M3 Pro - Space Gray", '{"color":"space gray","processor":"M3 Pro","screen":"14 inch"}', "1234567890129", True],
)

vitamin_c_variant_id = insert_variant(
    "INSERT INTO public.product_variants (product_id, sku, variant_name, attributes, barcode, is_active) "
    "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
    [vitamin_c_serum_id, "VITC-SERUM-30ML", "30ml", '{"size":"30ml"}', "1234567890130", True],
)

# ── Product Prices ──────────────────────────────────────────────────────
cur.execute(
    "INSERT INTO public.product_prices (variant_id, currency_code, selling_price, compare_at_price, effective_from, effective_until, is_active) "
    "VALUES (%s, %s, %s, %s, NOW(), NULL, %s)",
    [iphone_variant_id, "BDT", 125000.00, 135000.00, True],
)

cur.execute(
    "INSERT INTO public.product_prices (variant_id, currency_code, selling_price, compare_at_price, effective_from, effective_until, is_active) "
    "VALUES (%s, %s, %s, %s, NOW(), NULL, %s)",
    [macbook_variant_id, "BDT", 185000.00, 195000.00, True],
)

cur.execute(
    "INSERT INTO public.product_prices (variant_id, currency_code, selling_price, compare_at_price, effective_from, effective_until, is_active) "
    "VALUES (%s, %s, %s, %s, NOW(), NULL, %s)",
    [vitamin_c_variant_id, "BDT", 899.00, 1199.00, True],
)

# ── Inventory Balances ──────────────────────────────────────────────────
cur.execute(
    "INSERT INTO public.inventory_balances (warehouse_id, variant_id, quantity_on_hand, quantity_reserved, updated_at) "
    "VALUES (%s, %s, %s, %s, NOW())",
    [best_gadget_warehouse_id, iphone_variant_id, 50, 0],
)

cur.execute(
    "INSERT INTO public.inventory_balances (warehouse_id, variant_id, quantity_on_hand, quantity_reserved, updated_at) "
    "VALUES (%s, %s, %s, %s, NOW())",
    [best_gadget_warehouse_id, macbook_variant_id, 50, 0],
)

cur.execute(
    "INSERT INTO public.inventory_balances (warehouse_id, variant_id, quantity_on_hand, quantity_reserved, updated_at) "
    "VALUES (%s, %s, %s, %s, NOW())",
    [aura_skin_care_warehouse_id, vitamin_c_variant_id, 50, 0],
)

CONN.commit()

# ── Output Summary ──────────────────────────────────────────────────────
print("=" * 60)
print("SEED DATA INSERTED SUCCESSFULLY")
print("=" * 60)
print()
print(f"Best Gadget Store ID: {best_gadget_id}")
print(f"Aura Skin Care Store ID: {aura_skin_care_id}")
print()
print(f"Warehouses:")
print(f"  Best Gadget: {best_gadget_warehouse_id}")
print(f"  Aura Skin Care: {aura_skin_care_warehouse_id}")
print()
print(f"Categories:")
print(f"  Smartphones: {smartphones_cat_id} (Best Gadget)")
print(f"  Laptops: {laptops_cat_id} (Best Gadget)")
print(f"  Face Wash: {face_wash_cat_id} (Aura Skin Care)")
print()
print("PRODUCTS & VARIANTS:")
print("-" * 60)
print(f"1. iPhone 15")
print(f"   Product ID:   {iphone_15_id}")
print(f"   Variant ID:   {iphone_variant_id}")
print(f"   SKU: IPHONE-15-128GB | Qty: 50")
print()
print(f"2. MacBook Pro")
print(f"   Product ID:   {macbook_pro_id}")
print(f"   Variant ID:   {macbook_variant_id}")
print(f"   SKU: MACBOOK-M3-14 | Qty: 50")
print()
print(f"3. Vitamin C Serum")
print(f"   Product ID:   {vitamin_c_serum_id}")
print(f"   Variant ID:   {vitamin_c_variant_id}")
print(f"   SKU: VITC-SERUM-30ML | Qty: 50")
print()
print("VARIANT IDs for Swagger UI POST /api/v1/cart/items:")
print(f"  iPhone 15:        {iphone_variant_id}")
print(f"  MacBook Pro:      {macbook_variant_id}")
print(f"  Vitamin C Serum:  {vitamin_c_variant_id}")
print("=" * 60)

cur.close()
CONN.close()