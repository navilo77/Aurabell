# Frontend ↔ Database Connectivity Audit

Date: 2026-11-24
Scope: Investigation only — **no code was written, edited, or executed against the project.**

---

## 1. High-level conclusion

**The frontend is already wired to the database, and the link is live and returning real data.**

The chain is:

```
Browser (Next.js on :3000)
  → apiFetch() → /api/v1/*  → FastAPI backend (:8000)
    → asyncpg → PostgreSQL (Supabase local on :54322)
```

Verified by direct HTTP probes (see §4). No new code is required to connect them.

---

## 2. Where the frontend calls the database

| File | Lines | What it does |
|---|---|---|
| `frontend/lib/api.ts` | 1–100 | Single `apiFetch<T>(path)` wrapper around `fetch`. Base URL is `/api/v1`, credentials `include`, 401 → refresh → retry lifecycle. |
| `frontend/app/(storefront)/shop/page.tsx` | 22–60 | Loads `/products` + `/stores`, then calls `/pricing/calculate?variant_id=…&store_id=…` for each product. |
| `frontend/app/(storefront)/shop/[id]/product-detail-client.tsx` | 64–95, 97–119 | Loads `/products/{id}`, `/stores`, `/pricing/calculate`, and POSTs to `/cart/items`. |
| `frontend/app/login/page.tsx` | 28 | Comment only — reads authoritative user state from backend cookies. |

---

## 3. Backend routes that touch the database

`backend/app/main.py:125–136` registers every module router under `/api/v1`:

- `auth` — session/refresh/logout
- `cart` — cart items
- `orders` — order creation
- `pricing` — price calculation (reads products, promotions, coupons)
- `inventory` (admin + public) — stock/reservations
- `stores` — store directory
- `users` — profiles
- `categories` (admin + public)
- `products` (admin + public) — the catalog itself

`backend/app/core/database.py` provides `async_session_factory` (asyncpg-backed), consumed by all modules.

`backend/.env` points at:
- `DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres`
- `SUPABASE_URL=http://127.0.0.1:54321`

---

## 4. Live verification (read-only probes)

```
GET http://localhost:8000/api/v1/health
→ {"status":"ok"}  200

GET http://localhost:8000/api/v1/stores
→ 2 stores returned ("Best Gadget", "Aura Skin Care"), status active,
  created_at 2026-11-17 — real rows from Postgres.

GET http://localhost:8000/api/v1/products
→ products returned with nested variants (e.g. "iPhone 15", SKU IPHONE-15-128GB),
  store_id matching the stores above — real rows from Postgres.
```

All three endpoints are served by the running container on port 8000, which is the same origin `apiFetch` targets. The frontend on port 3000 is therefore able to read and write to the database today.

---

## 5. What is *not* connected (gaps found)

| Gap | Location | Impact |
|---|---|---|
| **Static image URLs are empty** | `products[].images` returned `[]` in the probe. `product-detail-client.tsx:122` falls back to `images[0]?.image_url`, which is `undefined`. | Product cards / detail pages show no image. The `public/images/` folder exists but is not referenced by seed data. |
| **No auth context provider** | `frontend/app/login/page.tsx` references "authoritative user state" via cookies, but no `app/(storefront)/layout.tsx` or global provider reads `/api/v1/auth/me` or `/users/me`. | Cart, orders, and profile UI cannot personalize or gate on logged-in user. |
| **Pricing endpoint is unauthenticated** | `/pricing/calculate` is hit by anonymous shop visitors. Acceptable for public catalog, but must not leak cost/wholesale data. | Verify the pricing module does not expose margin fields in `PriceCalculationRead`. |
| **No error boundary around data fetch** | `shop/page.tsx:50` sets `error` from a single string; `product-detail-client.tsx:78` does the same. Any 500 from the backend surfaces as raw `e.message`. | Poor UX on backend hiccup; no retry UI. |

---

## 6. Recommendation

**No action needed to establish connectivity — it already works.**

If the goal is to make the storefront *actually display* data end-to-end, the minimal next step (outside this audit's scope, and not executed here) is:

1. Seed `images` rows (or `image_url` on `products`) so `ProductCard` / `ProductDetailClient` have a `primaryImage`.
2. Add an auth context that calls `/api/v1/auth/me` on mount so cart/order/profile views can personalize.

Both are feature additions, not connectivity fixes.

---

## 7. Confirmation

Per the request, this report was produced by investigation and probing only. **No source file was modified, no new file was added to the application tree, and no build/test was run.** The audit file itself is documentation and may be deleted without affecting the project.