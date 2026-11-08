---
id: DOC-AUR-064
title: Aura Bell — Database Architecture & Concurrency Strategy
type: technical
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001, AB-DS-001
last_updated: 2026-11-04
---

# Aura Bell — Database Architecture & Concurrency (ডাটাবেজ আর্কিটেকচার ও কনকারেন্সি)

## ১. ডাটাবেজ দর্শন
Supabase পরিচালিত একক PostgreSQL 15+ ইনস্ট্যান্স Aura Bell-এর সমস্ত ডেটার কেন্দ্রীয় ভান্ডার।

## ২. কনকারেন্সি ও ট্রানজ্যাকশন আইসোলেশন
* **চেকআউট ট্রানজ্যাকশন**: একই সাথে একাধিক গ্রাহক একই পণ্যের শেষ ইউনিট অর্ডার করার চেষ্টা করলে ডাটাবেজে `SELECT ... FOR UPDATE` রো-লকিং ব্যবহৃত হবে।
* **Zero Negative Stock Invariant**: `inventory_balances` টেবিলে `CHECK (quantity_on_hand >= 0)` এবং `CHECK (quantity_reserved >= 0)` বাধ্যতামূলক কনস্ট্রেইন্ট হিসেবে থাকবে।
* **ACID গ্যারান্টি**: প্যারেন্ট অর্ডার ও স্প্লিট অর্ডার তৈরির সমস্ত অপারেশন একটিমাত্র ট্রানজ্যাকশন ব্লকে এক্সিকিউট হবে; কোনো একটি অংশে ব্যর্থ হলে সম্পূর্ণ পরিবর্তন রোলব্যাক হবে।
