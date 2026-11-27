import psycopg2

conn = psycopg2.connect(host='127.0.0.1', port=54322, user='postgres', password='postgres', dbname='postgres')
cur = conn.cursor()
cur.execute("SELECT product_id, image_url, is_primary, sort_order FROM product_images;")
rows = cur.fetchall()
for r in rows:
    print(r)
cur.close()
conn.close()