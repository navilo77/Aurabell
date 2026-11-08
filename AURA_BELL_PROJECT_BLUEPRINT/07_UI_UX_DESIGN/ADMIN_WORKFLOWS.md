---
id: DOC-AUR-092
title: Aura Bell — Admin Operations & Backoffice Workflows
type: design
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001, AB-DS-001
last_updated: 2026-11-04
---

# Aura Bell — Admin Backoffice Workflows (এডমিন কর্মপ্রবাহ)

## ১. দৈনিক অর্ডার প্রসেসিং প্রবাহ
1. এডমিন প্যানেলে লগইন করে `Pending Orders` ফিল্টার করা।
2. নতুন অর্ডার রিভিউ করা এবং গ্রাহকের ঠিকানার সত্যতা নিশ্চিত করে `CONFIRMED` এ রূপান্তর করা।
3. ওয়্যারহাউস প্যাকিং স্লিপ প্রিন্ট করে পণ্য প্রস্তুত করা।
4. ম্যানুয়াল কুরিয়ার সিলেকশন (Steadfast/Pathao) করে ট্র্যাকিং আইডি এসাইন করা এবং স্ট্যাটাস `SHIPPED` এ নেওয়া।

## ২. ইনভেন্টরি অডিট ও ফিজিক্যাল কাউন্ট প্রবাহ
1. গুদামের প্রকৃত পণ্যের সংখ্যা গণনা করা।
2. ডাটাবেজের `quantity_on_hand`-এর সাথে অমিল থাকলে `Inventory Adjustment` স্ক্রিনে যেয়ে পার্থক্য ও নির্দিষ্ট কারণ (Damage, Lost, Physical Count Correction) লিখে সাবমিট করা।
3. ব্যাকএন্ড স্বয়ংক্রিয়ভাবে `stock_movements` লেজারে অডিট এন্ট্রি সংরক্ষণ করবে।
