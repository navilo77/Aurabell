import psycopg2
import sys

print("Starting script...", flush=True)
sys.stdout.flush()

try:
    print("Connecting to database...", flush=True)
    sys.stdout.flush()
    conn = psycopg2.connect(host='127.0.0.1', port=54322, user='postgres', password='postgres', dbname='postgres')
    print("Connected to database!", flush=True)
    sys.stdout.flush()
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"PostgreSQL version: {version}", flush=True)
    sys.stdout.flush()
    cur.execute("SELECT id, slug FROM products;")
    rows = cur.fetchall()
    print(f"Products found: {len(rows)}", flush=True)
    sys.stdout.flush()
    for r in rows:
        print(f"  {r}", flush=True)
        sys.stdout.flush()
    cur.close()
    conn.close()
    print("Done!", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)
    import traceback
    traceback.print_exc()