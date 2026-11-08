---
id: DOC-AUR-070
title: Aura Bell — Complete Database Schema Specification (43 Tables)
type: database
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-DS-001 (Google Docs: 11-qT675s8QXOKJSO5sIbzbhr4LXK7PYPH4d0pnnrUUs)
last_updated: 2026-11-04
---

# Aura Bell — Complete Database Schema (৪৩টি টেবিলের বিশদ স্কিমা)

Aura Bell প্ল্যাটফর্মের ডাটাবেজ মডেলটি ১১টি প্রধান ডোমেনে বিভক্ত ৪৩টি সুসংগঠিত রিলেশনাল টেবিল নিয়ে গঠিত।

---

## ১. আইডেন্টিটি ও ব্যবহারকারী ব্যবস্থাপনা (Identity & User Management)
1. `profiles`: ব্যবহারকারীর নাম, ফোন নম্বর, ডিফল্ট ভাষা ও মেটাডাটা।
2. `addresses`: গ্রাহকের একাধিক ডেলিভারি ও বিলিং ঠিকানা।
3. `roles`: সিস্টেমের রোলসমূহ (Super Admin, Store Manager, Customer ইত্যাদি)।
4. `permissions`: সুনির্দিষ্ট অ্যাকশন পারমিশন তালিকা।
5. `user_roles`: ব্যবহারকারী ও রোলের মেনি-টু-মেনি রিলেশন।
6. `role_permissions`: রোল ও অনুমোদনের ম্যাপ।

## ২. স্টোর ব্যবস্থাপনা (Store Management)
7. `stores`: স্টোরের মৌলিক তথ্য (Best Gadget, Aura Skin Care), স্লাগ ও স্ট্যাটাস।
8. `store_policies`: স্টোরভিত্তিক রিটার্ন, ওয়ারেন্টি ও টার্মস পলিসি।

## ৩. প্রোডাক্ট ক্যাটালগ (Product Catalog)
9. `categories`: প্যারেন্ট-চাইল্ড হায়ারার্কিকাল ক্যাটাগরি।
10. `products`: মূল প্রোডাক্ট এন্ট্রি ও বিবরণ।
11. `product_variants`: সাইজ, কালার বা ভলিউম ভিত্তিক স্বতন্ত্র এসকেইউ (SKU)।
12. `product_images`: পণ্যের ছবি ও ডিসপ্লে অর্ডার।
13. `product_attributes`: স্কিনকেয়ারের উপাদান বা গ্যাজেটের ওয়ারেন্টি মেটাডাটা।

## ৪. প্রাইসিং ও প্রমোশন (Pricing Management)
14. `product_prices`: ভ্যারিয়েন্টের বিক্রয় মূল্য, ক্রয়মূল্য ও অফার মূল্য।
15. `promotions`: কুপন কোড ও শতাংশ/নির্দিষ্ট ডিসকাউন্ট রুলস।

## ৫. ইনভেন্টরি ও ওয়্যারহাউস (Inventory Management)
16. `warehouses`: গুদাম বা আউটলেট লোকেশন।
17. `inventory_balances`: রিয়েলটাইম স্টক অন হ্যান্ড ও রিজার্ভড স্টক।
18. `stock_movements`: স্টকের প্রতিটি পরিবর্তন ও অডিটের ইমিউটেবল লেজার।
19. `inventory_reservations`: চেকআউটের সময় সাময়িক স্টক হোল্ড ও মেয়াদ।
20. `product_batches`: স্কিনকেয়ারের ব্যাচ নম্বর ও এক্সপায়ারি ডেট।
21. `product_serials`: গ্যাজেট পণ্যের সিরিয়াল বা IMEI নম্বর।

## ৬. শপিং কার্ট (Shopping Cart)
22. `carts`: ব্যবহারকারী বা সেশন কার্ট হেডার।
23. `cart_items`: কার্টের আইটেম, ভ্যারিয়েন্ট ও পরিমাণ।

## ৭. অর্ডার ব্যবস্থাপনা (Order Management)
24. `orders`: কেন্দ্রীয় প্যারেন্ট অর্ডার (মোট মূল্য ও পেমেন্ট অবস্থা)।
25. `store_orders`: নির্দিষ্ট স্টোরের আন্ডারে বিভক্ত চাইল্ড অর্ডার।
26. `order_items`: অর্ডারের মুহূর্তের আইটেম স্ন্যাপশট (মূল্য, নাম, এসকেইউ)।
27. `order_addresses`: অর্ডারের সময়ের ডেলিভারি ও বিলিং ঠিকানার স্ন্যাপশট।
28. `order_status_history`: অর্ডার স্ট্যাটাস পরিবর্তনের সম্পূর্ণ টাইমলাইন।

## ৮. পেমেন্ট ও অর্থায়ন (Payment & Financial Records)
29. `payments`: পেমেন্ট এটেম্পট ও মোট কালেকশন রেকর্ড।
30. `payment_transactions`: গেটওয়ে ট্রানজ্যাকশন আইডি ও মেটাডাটা।
31. `payment_webhook_events`: গেটওয়ের পাঠানো প্রতিটি ওয়েবহুকের অডিট লগ।
32. `refunds`: রিফান্ড রেকর্ড ও অনুমোদন ট্রেইল।
33. `expenses`: কুরিয়ার চার্জ, প্যাকিং ও বিবিধ ব্যবসায়িক খরচ।
34. `financial_entries`: আর্থিক ট্রানজ্যাকশন রিকনসিলিয়েশন রেকর্ড।

## ৯. শিপমেন্ট ও লজিস্টিকস (Delivery & Shipment)
35. `couriers`: কুরিয়ার প্রোভাইডার তালিকা (Steadfast, Pathao, RedX ইত্যাদি)।
36. `shipments`: প্রতিটি পার্সেলের ডেলিভারি রেকর্ড ও ট্র্যাকিং কোড।
37. `shipment_events`: ডেলিভারি টাইমলাইনের রিয়েলটাইম ইভেন্ট হিস্ট্রি।

## ১০. রিটার্ন ও গ্রাহক সেবা (Return & Customer Support)
38. `return_requests`: গ্রাহকের দাখিলকৃত পণ্য ফেরতের আবেদন।
39. `return_items`: ফেরতের জন্য নির্দিষ্ট আইটেম ও কারণ।
40. `support_tickets`: সাপোর্ট টিকেট হেডার ও স্ট্যাটাস।
41. `support_messages`: টিকেটের বার্তা আদান-প্রদান।

## ১১. সিস্টেম অপারেশনস (System Operations & Reports)
42. `audit_logs`: ব্যবহারকারী ও এডমিনের স্পর্শকাতর অপারেশনের লগ।
43. `outbox_events`: ব্যাকগ্রাউন্ড ওয়ার্কারের জন্য ট্রানজ্যাকশনাল ইভেন্ট।
44. `notifications`: ইন-অ্যাপ নোটিফিকেশন।
45. `notification_templates`: মেসেজ টেমপ্লেটস।
46. `idempotency_keys`: এপিআই ডুপ্লিকেট রিকোয়েস্ট রোধক কি।
47. `daily_reports`: দৈনিক বিক্রয়, কালেকশন ও স্টক ক্যাশ সামারি।
