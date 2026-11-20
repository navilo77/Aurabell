import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=54322, user='postgres', password='postgres', dbname='postgres')
cur = conn.cursor()
cur.execute("""
    SELECT p.name, pv.sku, pv.id AS variant_id, pp.selling_price, ib.quantity_on_hand, s.name AS store, w.name AS warehouse
    FROM public.product_variants pv
    JOIN public.products p ON pv.product_id = p.id
    JOIN public.stores s ON p.store_id = s.id
    LEFT JOIN public.product_prices pp ON pp.variant_id = pv.id AND pp.is_active = TRUE
    LEFT JOIN public.inventory_balances ib ON ib.variant_id = pv.id
    LEFT JOIN public.warehouses w ON ib.warehouse_id = w.id
    ORDER BY p.name
""")
rows = cur.fetchall()
print(f"{'Product':<18}{'SKU':<20}{'Store':<16}{'Price':>10}{'Stock':>7}  Warehouse")
print("-" * 95)
for r in rows:
    print(f"{r[0]:<18}{r[1]:<20}{r[4]:<16}{r[3] or 0:>10}{r[5] or 0:>7}  {r[6] or ''}")
print(f"\nTotal variants: {len(rows)}")
conn.close()