---
id: DOC-AUR-072
title: Aura Bell — Database Relationships & Foreign Key Cascades
type: database
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-DS-001, AB-DM-001
last_updated: 2026-11-04
---

# Database Relationships & Cascades (রিলেশনশিপ ও ক্যাস্কেডিং রুলস)

Aura Bell ডাটাবেজের সমস্ত রিলেশনে তথ্য মুছে যাওয়া বা অর্ফ্যান রেকর্ড তৈরি হওয়া রোধে স্পষ্ট ক্যাস্কেডিং নীতি অনুসরণ করা হয়েছে:

| প্যারেন্ট টেবিল | চাইল্ড টেবিল | ফরেন কি | অন ডিলিট রুল (ON DELETE) | যৌক্তিক ব্যাখ্যা |
|---|---|---|---|---|
| `stores` | `products` | `store_id` | `RESTRICT` | স্টোরে পণ্য থাকা অবস্থায় স্টোর মোছা সম্পূর্ণ নিষিদ্ধ। |
| `products` | `product_variants` | `product_id` | `CASCADE` | মূল প্রোডাক্ট ডিলিট হলে সংশ্লিষ্ট ভ্যারিয়েন্টগুলো ক্যাস্কেড হবে। |
| `orders` | `store_orders` | `order_id` | `RESTRICT` | মূল প্যারেন্ট অর্ডার ডিলিট নিষিদ্ধ; শুধুমাত্র স্ট্যাটাস CANCELLED হবে। |
| `store_orders` | `order_items` | `store_order_id`| `RESTRICT` | অর্ডার আইটেম হিস্ট্রি কখনো হারানো যাবে না। |
| `carts` | `cart_items` | `cart_id` | `CASCADE` | কার্ট খালি বা ক্লিয়ার হলে কার্ট আইটেম স্বয়ংক্রিয় মুছে যাবে। |
| `profiles` | `orders` | `customer_id` | `RESTRICT` | অতীত অর্ডার থাকা কোনো গ্রাহক অ্যাকাউন্ট ডাটাবেজ থেকে হার্ড-ডিলিট করা নিষিদ্ধ। |
