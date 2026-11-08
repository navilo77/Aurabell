---
id: DOC-AUR-043
title: Aura Bell — Multi-Store Engine PRD
type: prd
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001
last_updated: 2026-11-04
---

# Multi-Store Engine PRD

## ১. উদ্দেশ্য
একই ডাটাবেজ ও কোডবেসের ওপর ভিত্তি করে সম্পূর্ণ স্বাধীন স্টোর ফ্রন্টএন্ড এবং ব্যাকঅফিস লজিক পরিচালনা করা।

## ২. ফাংশনাল স্পেসিফিকেশন
* **PRD-STR-001 (Store Isolation)**: প্রতিটি স্টোরের জন্য ইউনিক `slug`, নাম, স্ট্যাটাস (`active`, `inactive`) ও কারেন্সি কনফিগারেশন।
* **PRD-STR-002 (Store Theming)**: ফ্রন্টএন্ডে Best Gadget ও Aura Skin Care-এর আলাদা কালার স্কিম ও ভিজ্যুয়াল আইডেন্টিটি রেন্ডারিং।
* **PRD-STR-003 (Store Policies)**: স্টোরভিত্তিক টার্মস, শিপিং টাইমলাইন এবং রিটার্ন উইন্ডো সংরক্ষণ।
