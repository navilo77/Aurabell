---
id: DOC-AUR-046
title: Aura Bell — Shared Cart & Unified Checkout PRD
type: prd
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001
last_updated: 2026-11-04
---

# Shared Cart & Checkout PRD

## ১. উদ্দেশ্য
মাল্টি-স্টোর অভিজ্ঞতাকে এক ছাতার নিচে এনে নিরবচ্ছিন্ন শপিং কার্ট ও এককালীন চেকআউট প্রবাহ সম্পন্ন করা।

## ২. ফাংশনাল স্পেসিফিকেশন
* **PRD-CHK-001 (Shared Cart)**: একাধিক স্টোরের পণ্য একই কার্টে যুক্ত রাখা (`carts` ও `cart_items` টেবিল)।
* **PRD-CHK-002 (Live Validation)**: কার্টে থাকা পণ্যগুলোর বর্তমান অ্যাক্টিভ স্ট্যাটাস ও স্টক রিয়েলটাইমে পরীক্ষা করা।
* **PRD-CHK-003 (Backend Price Authority)**: চেকআউট সাবমিশনের সময় ব্যাকএন্ড ডাটাবেজ থেকে প্রতিটি আইটেমের বর্তমান মূল্য টেনে মোট টোটাল হিসাব করবে।
* **PRD-CHK-004 (Delivery Fee Calculation)**: ফ্ল্যাট ডেলিভারি ফি (একই অর্ডারের জন্য একক শিপিং ফি) গণনা করা, ঠিকানা ও স্টোরের সংখ্যা নির্বিশেষে স্বচ্ছভাবে প্রদর্শন।
* **PRD-CHK-005 (Atomic Transaction)**: একটিমাত্র ডাটাবেজ ট্রানজ্যাকশনে প্যারেন্ট অর্ডার ও স্টোর অর্ডার তৈরি এবং স্টক রিজার্ভেশন সম্পন্ন করা।

