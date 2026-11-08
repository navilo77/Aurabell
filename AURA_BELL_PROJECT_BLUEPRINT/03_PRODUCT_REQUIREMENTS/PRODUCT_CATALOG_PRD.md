---
id: DOC-AUR-044
title: Aura Bell — Product Catalog & Categories PRD
type: prd
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001
last_updated: 2026-11-04
---

# Product Catalog PRD

## ১. উদ্দেশ্য
উভয় স্টোরের জন্য ডায়নামিক, এসইও-বান্ধব এবং বৈচিত্র্যময় পণ্য ক্যাটালগ ও ক্যাটাগরি হায়ারার্কি তৈরি করা।

## ২. ফাংশনাল স্পেসিফিকেশন
* **PRD-CAT-001 (Category Hierarchy)**: প্যারেন্ট-চাইল্ড ক্যাটাগরি ট্রি সাপোর্ট (`categories` টেবিল)।
* **PRD-CAT-002 (Product Management)**: নাম, স্লাগ, ডেসক্রিপশন, ব্র্যান্ড ও বেস প্রাইস ব্যবস্থাপনা।
* **PRD-CAT-003 (Variants & SKU)**: পণ্যের বিভিন্ন আকার, রঙ বা ভলিউমের জন্য স্বতন্ত্র এসকেইউ (SKU) তৈরি (`product_variants`)।
* **PRD-CAT-004 (Specialized Attributes)**: Skincare এর জন্য উপাদান (Ingredients), প্রয়োগের নিয়ম; Gadget এর জন্য স্পেসিফিকেশন ও ওয়ারেন্টি ডেটা (`product_attributes`)।
* **PRD-CAT-005 (Image Gallery)**: Supabase Storage এ সংরক্ষিত একাধিক ইমেজ এবং প্রাইমারি থাম্বনেইল নির্বাচন।
