# AURA BELL — কোডবেস সামগ্রিক অডিট ও রিস্ক অ্যাসেসমেন্ট রিপোর্ট
**Document ID**: `DOC-AUR-173`  
**তারিখ**: ১৭ নভেম্বর ২০২৬  
**সংস্করণ**: 1.0.0  
**স্ট্যাটাস**: চূড়ান্ত অডিট রিপোর্ট (Comprehensive Audit Report)  
**বিভাগ**: `11_QUALITY_ASSURANCE`  
**স্কোপ**: `backend/` সম্পূর্ণ পাইথন কোডবেস (FastAPI, Core, Auth, Inventory, Pricing, Products, Categories, Stores, Users, Database Migrations & Test Suites)

---

## ১. নির্বাহী সারসংক্ষেপ (Executive Summary)

Aura Bell মাল্টি-স্টোর ই-কমার্স প্ল্যাটফর্মের ব্যাকএন্ড কোডবেস (`backend/app/`, `backend/supabase/migrations/`, `backend/tests/`) গভীর ও পুঙ্খানুপুঙ্খভাবে স্ট্যাটিক এবং আর্কিটেকচারাল অডিট করা হয়েছে।

বর্তমান কোডবেসে **৭৮টি টেস্ট সফলভাবে পাস** হলেও, গভীর অডিটে এমন কিছু **ক্রিটিক্যাল রানটাইম বাগ (Runtime Crash Bugs)** এবং **নিরাপত্তা ও কনকারেন্সি ঝুঁকি** শনাক্ত হয়েছে যা টেস্ট স্যুটে ধরা পড়েনি—কারণ ৩টি প্রধান মডিউলের (`users`, `products`, `categories`) কোনো ইউনিট বা ইন্টিগ্রেশন টেস্ট টেস্ট স্যুটে উপস্থিত ছিল না।

### মূল ফলাফল ও পরিসংখ্যান (Audit Metrics)
- **মোট অডিটকৃত ফাইল**: ৭৩টি
- **ক্রিটিক্যাল ব্লকার বাগ (Critical/Blocker Bugs)**: ৪টি (তাত্ক্ষণিক রানটাইম ক্র্যাশ ও ইনফিনিট লুপ)
- **নিরাপত্তা ও অথরাইজেশন ঝুঁকি (Security & Auth Flaws)**: ৫টি (ক্রস-স্টোর ডেটা অ্যাক্সেস ও হার্ডকোডেড হোস্ট)
- **কনকারেন্সি ও ডেটা অখণ্ডতা ঝুঁকি (Concurrency Risks)**: ৩টি (ইনভেন্টরি লক অসঙ্গতি ও N+1 ব্যাকগ্রাউন্ড ক্লিয়ারেন্স)
- **পারফরম্যান্স ঘাটতি (Performance Bottlenecks)**: ৩টি (প্রোডাক্ট লিস্টিংয়ে N+1 কোয়েরি ও সিঙ্ক ক্লায়েন্ট ব্লকিং)
- **কোড কোয়ালিটি ও টেস্ট শূন্যতা (Quality & Test Gaps)**: ৩টি প্রধান মডিউলে টেস্ট কভারেজ ০%

---

## ২. ক্রিটিক্যাল রানটাইম ত্রুটি (Critical / Blocker Bugs)

### ত্রুটি ০১: `UsersService` মডিউলে ভুল SQLAlchemy সিনট্যাক্স (১০০% রানটাইম ক্র্যাশ)
- **ফাইল**: [users/service.py](file:///d:/navil/TCH/Aura%20bell/backend/app/modules/users/service.py#L32-L105)
- **তীব্রতা (Severity)**: 🔴 **CRITICAL / BLOCKER**
- **সমস্যা বিশ্লেষণ**:
  `backend/app/modules/users/service.py` ফাইলে `select()`, `update()`, `insert()`, এবং `delete()` ফাংশনগুলোতে স্ট্রিং টেবিল নাম পাস করা হয়েছে:
  ```python
  # লাইন ৩৩-৪৬:
  result = await self.db.execute(
      select("id", "email", ...).select_from("profiles").where("id = :user_id"),
      {"user_id": user.id},
  )
  # লাইন ৭২-৭৫:
  await self.db.execute(
      update("profiles").where("id = :user_id").values(**update_data),
      {"user_id": user.id},
  )
  ```
- **প্রভাব**:
  SQLAlchemy 2.0-এ এটি সরাসরি `sqlalchemy.exc.ArgumentError: Textual column expression 'id' should be explicitly declared with text('id')` এবং `subject table for an INSERT, UPDATE or DELETE expected, got 'profiles'` এরর দিয়ে ক্র্যাশ করে। ইউজার প্রোফাইল বা অ্যাড্রেসের যেকোনো এন্ডিং পয়েন্টে রিকোয়েস্ট করলেই সার্ভার ক্র্যাশ (HTTP 500) করবে।
- **কেন টেস্টে ধরা পড়েনি?**: `backend/tests/` ডিরেক্টরিতে `users` মডিউলের জন্য কোনো টেস্ট ফাইল নেই।
- **সমাধান**: অন্যান্য সার্ভিসগুলোর মতো সরাসরি `text("""SELECT ... FROM public.profiles WHERE ...""")` অথবা ORM Table কনস্ট্রাক্ট ব্যবহার করতে হবে।

---

### ত্রুটি ০২: `ProductsService` এ অসীম লুপ (Infinite Loop) ও NameError
- **ফাইল**: [products/service.py](file:///d:/navil/TCH/Aura%20bell/backend/app/modules/products/service.py#L77-L92)
- **তীব্রতা (Severity)**: 🔴 **CRITICAL / BLOCKER**
- **সমস্যা বিশ্লেষণ**:
  `_generate_unique_slug` মেথডের কোড স্ট্রাকচার:
  ```python
  async def _generate_unique_slug(self, store_id: str, base_slug: str) -> str:
      slug = base_slug
      counter = 1
      while True:
          existing = await self.db.execute(
              text("SELECT id FROM products WHERE store_id = :store_id AND slug = :slug"),
              {"store_id": store_id, "slug": slug},
          )
          if not existing.scalar_one_or_none():
              return slug
              slug = f"{base_sku}-{counter}"  # <-- Unreachable & NameError (base_sku নেই)!
          counter += 1
  ```
- **প্রভাব**:
  যদি একই স্টোরে একই নামের দ্বিতীয় কোনো প্রোডাক্ট তৈরি করা হয়, `slug` ভেরিয়েবল লুপের ভেতর কখনোই আপডেট হয় না (`slug` অপরিবর্তিত থাকে এবং `counter` শুধু বাড়তে থাকে)। ফলে সিস্টেম অসীম লুপে (`while True:`) আটকে যায়, ডাটাবেসে নিরবচ্ছিন্ন কোয়েরি পাঠিয়ে CPU ১০০% গ্রাস করবে এবং সার্ভার হ্যাং হয়ে যাবে! তাছাড়া ইনডেন্টেশন ভুলের কারণে `slug = f"{base_sku}-{counter}"` রিটার্ন স্টেটমেন্টের নিচে চলে গেছে যেখানে `base_sku` ডিফাইনই করা নেই।
- **সমাধান**:
  `categories/service.py` এর মতো সঠিক লজিক প্রয়োগ করতে হবে:
  ```python
  async def _generate_unique_slug(self, store_id: str, base_slug: str) -> str:
      slug = base_slug
      counter = 1
      while True:
          existing = await self.db.execute(
              text("SELECT id FROM products WHERE store_id = :store_id AND slug = :slug"),
              {"store_id": store_id, "slug": slug},
          )
          if not existing.scalar_one_or_none():
              return slug
          slug = f"{base_slug}-{counter}"
          counter += 1
  ```

---

### ত্রুটি ০৩: `security.py` এ `SUPABASE_URL` নাল চেক না থাকা (NoneType AttributeError)
- **ফাইল**: [core/security.py](file:///d:/navil/TCH/Aura%20bell/backend/app/core/security.py#L33-L43)
- **তীব্রতা (Severity)**: 🟠 **HIGH**
- **সমস্যা বিশ্লেষণ**:
  ```python
  def _get_jwks_url() -> str:
      base = settings.SUPABASE_URL.rstrip("/")
      return f"{base}/auth/v1/.well-known/jwks.json"
  ```
  যদি কোনো কারণে `settings.SUPABASE_URL` সেট না থাকে বা খালি থাকে (`None`), তবে এটি সরাসরি `AttributeError: 'NoneType' object has no attribute 'rstrip'` দিয়ে পুরো অথরাইজেশন পাইপলাইন ক্র্যাশ করাবে।
- **সমাধান**: `if not settings.SUPABASE_URL: raise AuthError("SUPABASE_URL not configured", status_code=500)` যুক্ত করা।

---

### ত্রুটি ০৪: `AuthService.logout` এ অপর্যাপ্ত টোকেন রিভোকেশন (Broken Logout)
- **ফাইল**: [auth/service.py](file:///d:/navil/TCH/Aura%20bell/backend/app/modules/auth/service.py#L134-L141)
- **তীব্রতা (Severity)**: 🟠 **HIGH**
- **সমস্যা বিশ্লেষণ**:
  ```python
  async def logout(self, access_token: str) -> None:
      try:
          self._client.auth.sign_out()
      except Exception:
          pass
  ```
  ফাংশনটিতে প্যারামিটার হিসেবে `access_token` নেওয়া হলেও, গ্লোবাল সিঙ্গলটন `self._client.auth.sign_out()` কল করা হয়েছে কোনো আর্গুমেন্ট ছাড়া। সিঙ্গলটন ক্লায়েন্টে কোনো নির্দিষ্ট ইউজারের সেশন স্টেট সংরক্ষিত থাকে না, ফলে নির্দিষ্ট ইউজারের টোকেন Supabase প্রান্তে রিভোক হয় না এবং লগআউট করার পরও টোকেন কার্যকর থেকে যায়।
- **সমাধান**: `admin_client` দিয়ে ইউজারের সেশন রিভোক করা অথবা ক্লায়েন্ট হেডারে অ্যাক্সেস টোকেন পাস করে সাইন-আউট রিকোয়েস্ট এক্সিকিউট করা।

---

## ৩. নিরাপত্তা ও মাল্টি-টেন্যান্ট অথরাইজেশন ফাঁকফোকর (Security & Authorization Vulnerabilities)

### ঝুঁকি ০৫: ক্রস-স্টোর আইসোলেশন নেই (Cross-Store Security Breach)
- **ফাইল**: [core/auth.py](file:///d:/navil/TCH/Aura%20bell/backend/app/core/auth.py#L111-L134), [products/router.py](file:///d:/navil/TCH/Aura%20bell/backend/app/modules/products/router.py#L46-L47)
- **তীব্রতা (Severity)**: 🔴 **CRITICAL**
- **সমস্যা বিশ্লেষণ**:
  - ডাটাবেস স্কিমা মাইগ্রেশনে (`20261113000001_001_core_identity.sql`), `user_roles` টেবিলে `store_id UUID` কলাম ডিফাইন করা রয়েছে। উদ্দেশ্য ছিল একজন ইউজার যেন নির্দিষ্ট একটি স্টোরের `store_manager` হতে পারেন।
  - কিন্তু ব্যাকএন্ডের `get_current_user` ডিপেনডেন্সিতে `ur.store_id` সম্পূর্ণ উপেক্ষা করে কেবল রোলের নামগুলো একটি সাধারণ লিস্টে (`User.roles = ["store_manager"]`) রাখা হয়।
  - পরবর্তীতে `products/router.py` বা অন্যান্য অ্যাডমিন রাউটারে:
    `_user = Depends(require_role("store_manager", "super_admin"))`
    চেক করা হয়।
- **প্রভাব**:
  স্টোর ১ (যেমন: Gadget Store) এর একজন স্টোর ম্যানেজার খুব সহজেই স্টোর ২ (যেমন: Skin Store) এর প্রোডাক্ট ক্রিয়েট, এডিট, বা ডিলিট করতে পারবেন (পেলোডে অন্য স্টোরের `store_id` পাঠিয়ে)। মাল্টি-টেন্যান্ট প্ল্যাটফর্মে এটি বিশাল নিরাপত্তা ত্রুটি।
- **সমাধান**: `User` ক্লাসে `store_ids: list[str]` সংরক্ষণ করা এবং প্রতিটি অ্যাডমিন এন্ডপয়েন্টে ভ্যালিডেট করা যে রিকোয়েস্টকৃত `store_id` ওই ইউজারের ম্যানেজড স্টোর তালিকার অন্তর্ভুক্ত কি না।

---

### ঝুঁকি ০৬: নতুন ইউজারদের অপ্রত্যাশিত আনঅথরাইজড লকআউট (Inner Join Issue)
- **ফাইল**: [core/auth.py](file:///d:/navil/TCH/Aura%20bell/backend/app/core/auth.py#L111-L127)
- **তীব্রতা (Severity)**: 🟠 **HIGH**
- **সমস্যা বিশ্লেষণ**:
  ```sql
  SELECT p.id, p.email, r.name as role_name
  FROM public.profiles p
  JOIN public.user_roles ur ON ur.user_id = p.id
  JOIN public.roles r ON r.id = ur.role_id
  WHERE p.id = :user_id
  ```
  কোয়েরিটিতে `INNER JOIN` ব্যবহার করা হয়েছে। কোনো সাধারণ কাস্টমার যখন সাইন-আপ করবেন এবং তার প্রোফাইল তৈরি হবে, কিন্তু `user_roles` টেবিলে অ্যাডমিন বা অটোমেশন এখনো কোনো রোল অ্যাসাইন করেনি, তখন কোয়েরি ০টি রো রিটার্ন করবে।
- **প্রভাব**:
  সিস্টেম সাথে সাথে `HTTPException(401, detail="User not found")` থ্রো করবে! একজন সফলভাবে নিবন্ধিত ইউজার তার প্রোফাইল বা কার্ট কোনো কিছুই অ্যাক্সেস করতে পারবেন না।
- **সমাধান**: `LEFT JOIN public.user_roles` ও `LEFT JOIN public.roles` ব্যবহার করা এবং কোনো রোল না থাকলে ডিফল্টভাবে `roles = ["customer"]` প্রদান করা।

---

### ঝুঁকি ০৭: হার্ডকোডেড হোস্ট, অরিজিন ও ডেভেলপমেন্ট ডেঞ্জার
- **ফাইল**: [main.py](file:///d:/navil/TCH/Aura%20bell/backend/app/main.py#L84-L115)
- **তীব্রতা (Severity)**: 🟡 **MEDIUM**
- **সমস্যা বিশ্লেষণ**:
  1. `TrustedHostMiddleware`: `allowed_hosts=["localhost", "127.0.0.1", "*.localhost", "testserver"]` হার্ডকোডেড। প্রোডাকশনে বা ডকারে ডেপ্লয় করলে রিয়েল ডোমেন বা আইপি থেকে আসা সমস্ত রিকোয়েস্ট রিজেক্ট হবে।
  2. `CORSMiddleware`: `allow_origins=["http://localhost:3000", ...]` হার্ডকোডেড। লাইভ ফ্রন্টএন্ড বা স্টেজিং ডোমেন থেকে রিকোয়েস্ট ব্লক হবে।
  3. `SessionMiddleware`: সিক্রেট কি হিসেবে `settings.SUPABASE_SERVICE_ROLE_KEY or "dev-secret-change-in-production"` এবং `https_only=False` হার্ডকোডেড।
  4. গ্লোবাল HSTS মিডলওয়্যার লোকাল HTTP রিকোয়েস্টেও পাঠানো হচ্ছে, যা ব্রাউজারকে `http://localhost:8000` এ HTTPS ফোর্স করতে বাধ্য করতে পারে।
- **সমাধান**: পরিবেশ ভ্যারিয়েবল (`settings.ALLOWED_HOSTS`, `settings.CORS_ORIGINS`, `settings.SESSION_SECRET_KEY`) থেকে কনফিগারেশন লোড করা।

---

## ৪. কনকারেন্সি ও ডেটা অখণ্ডতা ঝুঁকি (Concurrency & Data Integrity Risks)

### ঝুঁকি ০৮: ইনভেন্টরি রিলিজে লক না থাকা (Missing Lock on Balance Release)
- **ফাইল**: [inventory/service.py](file:///d:/navil/TCH/Aura%20bell/backend/app/modules/inventory/service.py#L446-L452)
- **তীব্রতা (Severity)**: 🟠 **HIGH**
- **সমস্যা বিশ্লেষণ**:
  `create_reservation` এবং `consume_reservation` মেথডগুলোতে `inventory_balances` টেবিলের রো `FOR UPDATE` দিয়ে লক করা হয় যাতে স্টক ওভারসেলিং না ঘটে। কিন্তু `release_reservation` মেথডে কোনো লক না নিয়েই সরাসরি:
  ```python
  UPDATE inventory_balances SET quantity_reserved = quantity_reserved - :qty ...
  ```
  এক্সিকিউট করা হয়।
- **প্রভাব**:
  একই সাথে একজন ইউজারের অর্ডার বাতিল বা টাইমআউট হওয়া এবং অন্য ইউজারের কার্ট চেকআউট কনকারেন্টলি ঘটলে রেস কন্ডিশন (Race Condition) তৈরি হয়ে ব্যালেন্স হিসাব উল্টাপাল্টা হতে পারে অথবা ডাটাবেস ডেডলক (Deadlock) তৈরি হবে।
- **সমাধান**: `release_reservation`-এও ব্যালেন্স রোটি আগে `FOR UPDATE` দিয়ে লক করা।

---

### ঝুঁকি ০৯: ব্যাকগ্রাউন্ড রিজার্ভেশন ক্লিয়ারেন্সে N+1 কোয়েরি ও সাইলেন্ট এক্সেপশন
- **ফাইল**: [main.py](file:///d:/navil/TCH/Aura%20bell/backend/app/main.py#L48-L50), [inventory/service.py](file:///d:/navil/TCH/Aura%20bell/backend/app/modules/inventory/service.py#L480-L525)
- **তীব্রতা (Severity)**: 🟠 **HIGH**
- **সমস্যা বিশ্লেষণ**:
  1. `main.py` এ ব্যাকগ্রাউন্ড ক্লিনিং টাস্কে:
     ```python
     except Exception:
         # Keep the worker alive across transient failures.
         pass
     ```
     কোনো লগার (`logger.exception`) নেই। যদি ডাটাবেস কানেকশন হারিয়ে যায় বা কোনো বাগ থাকে, সিস্টেম নিরবে ফেইল করবে এবং ডেভেলপাররা কখনোই ত্রুটি সম্পর্কে জানতে পারবেন না।
  2. `cleanup_expired_reservations` মেথডে এক্সপায়ার হওয়া সমস্ত রিজার্ভেশন লুপ চালিয়ে একটি একটি করে আপডেট ও মুভমেন্ট লেজার তৈরি করে (প্রতিটি রিজার্ভেশনের জন্য ৩টি পৃথক কোয়েরি)।
- **প্রভাব**:
  অর্ডারের পিক আওয়ারে শত শত এক্সপায়ার হওয়া কার্ট একসঙ্গে ক্লিন করতে গেলে N+1 কোয়েরি ফ্ল্যাড হবে এবং ডাটাবেস কানেকশন পুল চোক করে ফেলবে।
- **সমাধান**: ত্রুটিটি লগে রেকর্ড করা এবং ক্লিনিং অপারেশনটি সিঙ্গেল ব্যাচ কোয়েরি বা CTE (Common Table Expression) দিয়ে অপটিমাইজ করা।

---

## ৫. পারফরম্যান্স ও স্কেলেবিলিটি ঘাটতি (Performance & Scalability Bottlenecks)

### ঝুঁকি ১০: পাবলিক প্রোডাক্ট লিস্টিংয়ে ক্লাসিক N+1 কোয়েরি বিপর্যয়
- **ফাইল**: [products/service.py](file:///d:/navil/TCH/Aura%20bell/backend/app/modules/products/service.py#L419-L425)
- **তীব্রতা (Severity)**: 🟠 **HIGH**
- **সমস্যা বিশ্লেষণ**:
  ```python
  products: list[ProductRead] = []
  for row in rows:
      pid = str(row["id"])
      variants = await self._get_variants(pid)  # পৃথক কোয়েরি
      images = await self._get_images(pid)      # পৃথক কোয়েরি
      products.append(self._row_to_read(row, variants, images))
  return products
  ```
- **প্রভাব**:
  ফ্রন্টএন্ডে যখন কোনো স্টোরের প্রোডাক্ট লিস্ট দেখানো হবে (ধরা যাক পেজ সাইজ ২০), তখন সার্ভার ১টি মেইন কোয়েরি + ২০টি ভ্যারিয়েন্ট কোয়েরি + ২০টি ইমেজ কোয়েরি = **মোট ৪১টি পৃথক ডাটাবেস নেটওয়ার্ক রাউন্ডট্রিপ** চালাবে! ১০০টি প্রোডাক্ট হলে ২০১টি কোয়েরি! এটি পেজ লোড টাইম অত্যন্ত ধীর করে দেবে।
- **সমাধান**: `LEFT JOIN` বা `WHERE product_id IN (...)` দিয়ে ব্যাচ ফেচ করে মেমোরিতে ম্যাপ করা।

---

### ঝুঁকি ১১: ডাটাবেস কানেকশন পুল আনটিউনড (Default Pool Exhaustion)
- **ফাইল**: [core/database.py](file:///d:/navil/TCH/Aura%20bell/backend/app/core/database.py#L20-L24)
- **তীব্রতা (Severity)**: 🟡 **MEDIUM**
- **সমস্যা বিশ্লেষণ**:
  SQLAlchemy-তে ইঞ্জিন তৈরির সময় `pool_size` ও `max_overflow` উল্লেখ করা নেই। ডিফল্টভাবে SQLAlchemy এর `pool_size=5` এবং `max_overflow=10`।
- **প্রভাব**:
  একযোগে ১৫ জনের বেশি কনকারেন্ট রিকোয়েস্ট এলেই `TimeoutError: QueuePool limit exceeded` ঘটবে।
- **সমাধান**: প্রোডাকশনের জন্য `pool_size=20`, `max_overflow=10`, `pool_timeout=30`, `pool_recycle=1800` কনফিগার করা।

---

### ঝুঁকি ১২: অ্যাসিনক্রোনাস লুপে সিনক্রোনাস Supabase ক্লায়েন্ট কল (Event Loop Blocking)
- **ফাইল**: [auth/service.py](file:///d:/navil/TCH/Aura%20bell/backend/app/modules/auth/service.py#L30-L45)
- **তীব্রতা (Severity)**: 🟡 **MEDIUM**
- **সমস্যা বিশ্লেষণ**:
  `AuthService` এ ব্যবহৃত অফিশিয়াল Supabase পাইথন SDK (`create_client`) মূলত সিনক্রোনাস HTTP ক্লায়েন্ট। এটি অ্যাসিনক্রোনাস FastAPI এন্ডপয়েন্টের ভেতরে সরাসরি কল করা হচ্ছে (`self._client.auth.sign_in_with_password(...)`)।
- **প্রভাব**:
  একজনের লগইন রিকোয়েস্ট প্রসেস হওয়া পর্যন্ত FastAPI-এর মূল অ্যাসিনক্রোনাস ইভেন্ট লুপ আটকে থাকে (Thread blocking), ফলে প্ল্যাটফর্মের থ্রুপুট কমে যায়।
- **সমাধান**: `asyncio.to_thread` ব্যবহার করে সিনক্রোনাস ক্লায়েন্ট কলকে ব্যাকগ্রাউন্ড থ্রেড পুলে ডেলিগেট করা অথবা সরাসরি অ্যাসিনক্রোনাস HTTPX দিয়ে Supabase GoTrue REST API কল করা।

---

## ৬. কোড কোয়ালিটি ও টেকনিক্যাল ডেট (Code Quality & Technical Debt)

### ঝুঁকি ১৩: ৩টি প্রধান মডিউলে কোনো টেস্ট না থাকা (Zero Test Coverage)
- **মডিউল**: `products`, `categories`, `users`
- **তীব্রতা (Severity)**: 🟠 **HIGH**
- **বিশ্লেষণ**:
  `backend/tests/` ডিরেক্টরিতে শুধুমাত্র `auth`, `inventory`, `pricing`, `stores`, এবং `seed` টেস্ট করা হয়েছে। `products`, `categories`, এবং `users` মডিউলের জন্য কোনো একক টেস্ট ফাইলও নেই। ফলে পূর্বোক্ত সিনট্যাক্স এরর ও অসীম লুপ টেস্টে আনডিটেক্টেড থেকে গেছে।
- **প্রয়োজনীয় পদক্ষেপ**: দ্রুত `test_products.py`, `test_categories.py`, এবং `test_users.py` তৈরি করা।

---

### ঝুঁকি ১৪: পাইথন ৩.১২+ এ অবলুপ্ত `datetime.utcnow()` এর ব্যবহার
- **ফাইল**: `products/service.py`, `categories/service.py`, `stores/service.py`, `users/service.py`
- **তীব্রতা (Severity)**: 🟢 **LOW**
- **বিশ্লেষণ**:
  কোডবেসের বহু জায়গায় `datetime.utcnow()` ব্যবহার করা হয়েছে। পাইথন ৩.১২ থেকে `datetime.utcnow()` অবলুপ্ত (Deprecated) ঘোষণা করা হয়েছে এবং ভবিষ্যতে এটি বাদ দেওয়া হবে।
- **সমাধান**: এর পরিবর্তে `datetime.now(timezone.utc)` ব্যবহার করা।

---

## ৭. মাইলস্টোন ৪ (M4) প্রস্তুতির ঘাটতিসমূহ (Roadmap Gap Analysis)

মাইলস্টোন ৪-এর মূল বিষয় হলো **কার্ট, চেকআউট এবং স্প্লিট-অর্ডার (Cart, Checkout & Split-Order Engine)**। বর্তমান কোডবেস অডিটে নিচের বিষয়গুলো লক্ষ করা গেছে:

1. **কার্ট মডিউল অনুপস্থিত**: `app/modules/cart/` এখনও তৈরি হয়নি।
2. **অর্ডার ও স্প্লিট-অর্ডার অনুপস্থিত**: মাল্টি-স্টোর অর্ডারের ক্ষেত্রে বিভিন্ন স্টোরের জন্য সাব-অর্ডার স্প্লিটিং ইঞ্জিন এখনো শুরু হয়নি।
3. **কাস্টমার চেকআউট রিজার্ভেশন এপিআই নেই**: বর্তমানে `inventory/router.py` তে রিজার্ভেশন তৈরি শুধুমাত্র `inventory_manager` বা `super_admin` রোলে সীমাবদ্ধ। একজন সাধারণ ক্রেতা যখন চেকআউট শুরু করবেন, তখন সিস্টেম ব্যাকগ্রাউন্ডে কার্ট আইটেমগুলোর জন্য ১৫ মিনিটের স্টক রিজার্ভেশন কীভাবে করবে, তার জন্য কাস্টমার-অথোরাইজড বা ইন্টারনাল সার্ভিস এপিআই প্রয়োজন।

---

## ৮. অগ্রাধিকারভিত্তিতে অ্যাকশন প্ল্যান (Prioritized Remediation Matrix)

| অগ্রাধিকার | সমস্যা / টাস্ক | আক্রান্ত ফাইল | প্রস্তাবিত সমাধান |
|---|---|---|---|
| **P0 (Immediate)** | Users মডিউলের ভুল সিনট্যাক্স ফিক্স | `app/modules/users/service.py` | `text()` দিয়ে কোয়েরি রিরাইট করা |
| **P0 (Immediate)** | Products এ অসীম লুপ ও NameError ফিক্স | `app/modules/products/service.py` | `_generate_unique_slug` লজিক ও ইনডেন্টেশন ফিক্স |
| **P0 (Immediate)** | Security-তে SUPABASE_URL নাল হ্যান্ডলিং | `app/core/security.py` | ডিফেন্সিভ নাল চেক যুক্ত করা |
| **P1 (High)** | মাল্টি-টেন্যান্ট স্টোর আইসোলেশন | `app/core/auth.py`, Admin Routers | `User` মডেলে `store_id` এনফোর্স করা |
| **P1 (High)** | নতুন ইউজারের জন্য Left Join Auth ফিক্স | `app/core/auth.py` | `LEFT JOIN user_roles` ও ডিফল্ট রোল প্রদান |
| **P1 (High)** | ইনভেন্টরি রিলিজ ও ক্লিনিং কনকারেন্সি ফিক্স | `app/modules/inventory/service.py` | `FOR UPDATE` লক যুক্ত করা ও ব্যাচ ক্লিয়ারেন্স |
| **P1 (High)** | প্রোডাক্ট লিস্টিং N+1 কোয়েরি অপটিমাইজেশন | `app/modules/products/service.py` | ব্যাচ/জয়েন কোয়েরি দিয়ে ভ্যারিয়েন্ট ও ইমেজ ফেচ |
| **P2 (Medium)** | মিসিং টেস্ট স্যুট তৈরি | `backend/tests/` | `test_users.py`, `test_products.py`, `test_categories.py` লেখা |
| **P2 (Medium)** | কনফিগারেশন হার্ডকোডিং মুক্ত করা | `app/main.py`, `app/core/config.py` | পরিবেশ ভ্যারিয়েবল সাপোর্ট যুক্ত করা |
| **P2 (Medium)** | কানেকশন পুল টিউনিং | `app/core/database.py` | `pool_size=20, max_overflow=10` সেট করা |
| **P3 (Low)** | `datetime.utcnow()` ক্লিনআপ | All Service Files | `datetime.now(timezone.utc)` এ রূপান্তর |

---

## ৯. উপসংহার (Conclusion)

Aura Bell প্ল্যাটফর্মের প্রাথমিক আর্কিটেকচার এবং ডাটাবেস ডিজাইন অত্যন্ত সুসংগঠিত। তবে কোডবেসে উপস্থিত ৪টি ক্রিটিক্যাল ব্লকার বাগ এবং টেস্ট কভারেজের শূন্যতা অবিলম্বে দূর করা প্রয়োজন। এই অডিট রিপোর্টের সুপারিশ অনুযায়ী P0 এবং P1 সমস্যাগুলো সমাধান করার পরেই মাইলস্টোন ৪ (কার্ট ও চেকআউট) এর মূল কোডিং শুরু করা নিরাপদ হবে।
