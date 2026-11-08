---
id: DOC-AUR-047
title: Aura Bell — Parent Order & Split Store Orders PRD
type: prd
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001
last_updated: 2026-11-04
---

# Order Management PRD

## ১. উদ্দেশ্য
প্যারেন্ট এবং স্টোর অর্ডারের স্প্লিট আর্কিটেকচার দক্ষতার সাথে পরিচালনা করা।

## ২. ফাংশনাল স্পেসিফিকেশন
* **PRD-ORD-001 (Parent Order Creation)**: চেকআউট সম্পন্ন হলে ইউনিক অর্ডার নম্বর সংবলিত একটি `orders` রেকর্ড তৈরি হবে।
* **PRD-ORD-002 (Store Order Splitting)**: প্রতিটি স্টোরের পণ্যের জন্য সংশ্লিষ্ট স্টোরের অধীনস্থ `store_orders` রেকর্ড তৈরি হবে।
* **PRD-ORD-003 (Order Item Snapshots)**: প্রতিটি আইটেমের নাম, এসকেইউ এবং পারচেজ প্রাইস স্ন্যাপশট হিসেবে সংরক্ষণ করা হবে (`order_items`)।
* **PRD-ORD-004 (State Lifecycle)**: `PENDING` ➡️ `CONFIRMED` ➡️ `PROCESSING` ➡️ `COMPLETED` বা `CANCELLED` জীবনচক্র পরিচালনা।
* **PRD-ORD-005 (Status History)**: প্রতিটি স্ট্যাটাস পরিবর্তনের সময়, পরিবর্তনকারী ইউজার ও নোট `order_status_history` টেবিলে লিপিবদ্ধ করা।
