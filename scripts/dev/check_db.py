import psycopg2

try:
    conn = psycopg2.connect(host='127.0.0.1', port=54322, user='postgres', password='postgres', dbname='postgres')
    print("Connected to database!")
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"PostgreSQL version: {version}")
    cur.execute("SELECT id, slug FROM products;")
    rows = cur.fetchall()
    print(f"Products found: {len(rows)}")
    for r in rows:
        print(f"  {r}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")