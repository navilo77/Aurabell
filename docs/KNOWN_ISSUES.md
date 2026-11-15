# Known Issues

Issues discovered during M2.1 (Store Management & Policy Engine) work.
Each entry records what was found, severity, status, and the planned fix.

---

## 2026-11-15 — users/service.py SQLAlchemy 2.0 incompatibility

- **Found during:** M2.1 Step 2.5 (stores service refactor)
- **Severity:** HIGH — all users endpoints crash at runtime
- **Status:** Deferred — out of M2.1 scope
- **Fix:** Same pattern as stores fix (text() refactor)
- **Blocks:** M6.3 admin dashboard (needs users list)
- **Scheduled for:** M2.5 or M1.3 debt cleanup milestone

**Detail:** `users/service.py` uses the same broken pattern as the original
`stores/service.py`:
```python
select("id", "email", ...).select_from("profiles").where("id = :user_id")
```
SQLAlchemy 2.0 rejects raw string column expressions. The file even carries
the comment `# Using raw SQL since we don't have ORM models yet`.
It is masked today because no test exercises the users endpoints, exactly
as `stores/service.py` was masked before Step 2.5.

---

## 2026-11-15 — stores/router.py was UTF-16LE encoded (binary in git)

- **Found during:** M2.1 Step 2 (make list_stores public)
- **Severity:** HIGH — router.py could not be compiled or imported
- **Status:** FIXED in commit f888f76 (converted to UTF-8)
- **Fix:** Decoded UTF-16LE → UTF-8, lossless (302 lines preserved)

**Detail:** `router.py` was the only file in the repo encoded as UTF-16LE
(BOM `fffe`, null byte every other character). Git treated it as binary.
Python could not compile it (`SyntaxError: source code string cannot contain
null bytes`). The 20 stores tests passed only because they import
`StoresService` from `service.py` and never import `router.py`. The FastAPI
app itself would fail at startup on `app.include_router(stores_router, ...)`.

---

## 2026-11-15 — text() returns native datetime; StoreRead/PolicyRead expect str

- **Found during:** M2.1 Step 2.5 E2E verification (uvicorn + curl)
- **Severity:** MEDIUM — list_stores returned 500 after the text() refactor
- **Status:** FIXED in commit e1bceb9 (wrap created_at/updated_at in str())
- **Fix:** `created_at=str(row["created_at"])`, `updated_at=str(row["updated_at"])`

**Detail:** After migrating to `text()`, SQLAlchemy returns native
`datetime` objects for `created_at`/`updated_at`, but `StoreRead` and
`PolicyRead` declare those fields as `str | None`. Pydantic raised
`ValidationError: Input should be a valid string`. The old string-based
`select()` code masked this because it never reached the response mapping
(it crashed earlier on the SQLAlchemy 2.0 ArgumentError). Consistent with
how `id`/`store_id` were already wrapped in `str()`.