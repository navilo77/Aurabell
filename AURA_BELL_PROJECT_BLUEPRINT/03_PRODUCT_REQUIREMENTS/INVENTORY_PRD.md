---
id: DOC-AUR-045
title: Aura Bell — Inventory, Ledger & Reservations PRD
type: prd
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001
last_updated: 2026-11-04
---

# Inventory Management PRD

## ১. উদ্দেশ্য
জিরো ওভারসেলিং, অ্যাটমিক রিজার্ভেশন এবং শতভাগ অডিটযোগ্য ডিজিটাল স্টক লেজার নিশ্চিত করা।

## ২. ফাংশনাল স্পেসিফিকেশন
* **PRD-INV-001 (Realtime Balance)**: ওয়্যারহাউস ও ভ্যারিয়েন্ট ভিত্তিতে `quantity_on_hand` এবং `quantity_reserved` ট্র্যাকিং।
* **PRD-INV-002 (Stock Reservation)**: চেকআউটের সময় ১৫ মিনিটের জন্য স্টক রিজার্ভেশন তৈরি (`inventory_reservations`)।
* **PRD-INV-003 (TTL Expiry Release)**: ১৫ মিনিটের মধ্যে পেমেন্ট সম্পন্ন না হলে ব্যাকগ্রাউন্ড জব দ্বারা রিজার্ভেশন রিলিজ।
* **PRD-INV-004 (Immutable Ledger)**: প্রতিটি স্টকের আগমণ, বিক্রয়, রিটার্ন বা অ্যাডজাস্টমেন্টের জন্য `stock_movements` টেবিলে স্বয়ংক্রিয় এন্ট্রি।
* **PRD-INV-005 (Batch & Serial)**: স্কিনকেয়ারের জন্য এক্সপায়ারি ডেট ট্র্যাকিং এবং গ্যাজেটের জন্য সিরিয়াল/IMEI ট্র্যাকিং।
