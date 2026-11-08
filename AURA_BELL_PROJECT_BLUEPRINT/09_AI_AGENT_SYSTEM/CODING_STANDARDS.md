---
id: DOC-AUR-115
title: Aura Bell — Technical Coding Standards (Python, TS, SQL)
type: technical
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001
last_updated: 2026-11-04
---

# Coding Standards (প্রযুক্তিগত কোডিং স্ট্যান্ডার্ড)

## ১. ব্যাকএন্ড (Python / FastAPI)
* **স্ট্যান্ডার্ড**: PEP 8, Black ফরম্যাটিং, Ruff লিন্টিং।
* **টাইপ অ্যানোটেশন**: সমস্ত ফাংশন ও মেথডে টাইপ হিন্টিং বাধ্যতামূলক (`def create_order(...) -> OrderRead:`).
* **ডাটা ভ্যালিডেশন**: ইনপুট ও আউটপুট উভয়ের জন্যই Pydantic v2 `BaseModel` ব্যবহার করতে হবে।
* **অ্যাসিঙ্ক ডিসিপ্লিন**: আই/ও বা ডাটাবেজ অপারেশনের জন্য সর্বদা অ্যাসিঙ্ক মেথড (`async def`, `await session.execute(...)`) ব্যবহার করতে হবে।

## ২. ফ্রন্টএন্ড (Next.js / TypeScript / React)
* **স্ট্যান্ডার্ড**: ESLint, Prettier, TypeScript Strict Mode।
* **নামকরণ**: কম্পোনেন্টের ফাইলের নাম PascalCase (যেমন: `ProductCard.tsx`), ইউটিলিটি ফাইলের নাম camelCase (`formatCurrency.ts`)।
* **সিএসএস**: শুধুমাত্র Tailwind CSS ক্লাস ব্যবহার করুন; ইনলাইন `style={{...}}` পরিহার করুন।

## ৩. ডাটাবেজ (PostgreSQL / SQL)
* **নামকরণ**: সমস্ত টেবিল ও কলামের নাম লোয়ারকেস স্নেক-কেস (`snake_case`) এবং প্লুরাল টেবিল নাম (যেমন: `store_orders`)।
* **ফরেন কি**: সংশ্লিষ্ট টেবিলের নাম + `_id` (যেমন: `order_id`, `variant_id`)।
