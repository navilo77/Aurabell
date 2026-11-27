import psycopg2

conn = psycopg2.connect(host='127.0.0.1', port=54322, user='postgres', password='postgres', dbname='postgres')
cur = conn.cursor()

# Get product IDs
cur.execute("SELECT id FROM products WHERE slug = 'iphone-15';")
iphone_id = cur.fetchone()[0]
cur.execute("SELECT id FROM products WHERE slug = 'macbook-pro';")
macbook_id = cur.fetchone()[0]
cur.execute("SELECT id FROM products WHERE slug = 'vitamin-c-serum';")
vitamin_id = cur.fetchone()[0]

print(f"iPhone: {iphone_id}")
print(f"MacBook: {macbook_id}")
print(f"Vitamin C: {vitamin_id}")

# Insert images
images = [
    (iphone_id, 'https://picsum.photos/seed/iphone-15/800/800', 'iPhone 15 Blue', True, 0),
    (macbook_id, 'https://picsum.photos/seed/macbook-pro/800/800', 'MacBook Pro Space Gray', True, 0),
    (vitamin_id, 'https://picsum.photos/seed/vitamin-c-serum/800/800', 'Vitamin C Serum 30ml', True, 0),
]

for img in images:
    cur.execute(
        "INSERT INTO product_images (product_id, image_url, alt_text, is_primary, sort_order) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING RETURNING id;",
        img
    )
    result = cur.fetchone()
    if result:
        print(f"Inserted image for product {img[0]}: {result[0]}")
    else:
        print(f"Image for product {img[0]} already exists")

conn.commit()
cur.close()
conn.close()