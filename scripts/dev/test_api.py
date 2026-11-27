import requests
try:
    resp = requests.get('http://127.0.0.1:8000/api/v1/products', timeout=5)
    print('Status:', resp.status_code)
    products = resp.json()
    for p in products:
        print(f'Product: {p["name"]}, Images: {len(p.get("images", []))}')
        for img in p.get('images', []):
            print(f'  - {img["image_url"]} (primary: {img["is_primary"]})')
except Exception as e:
    print('Error:', e)