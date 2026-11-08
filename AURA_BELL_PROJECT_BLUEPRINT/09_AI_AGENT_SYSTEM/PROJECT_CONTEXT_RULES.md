---
id: DOC-AUR-114
title: Aura Bell — Project Context & Invariant Rules
type: instruction
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001
last_updated: 2026-11-04
---

# Project Context Rules (কনটেক্সট সংরক্ষণ ও ইনভ্যারিয়েন্ট রুলস)

1. **মাল্টি-স্টোর কনটেক্সট সবসময় সচল**: প্রতিটি অর্ডার লজিক ও ক্যাটালগ রিকোয়েস্টে স্টোর আইডেন্টিটি (`store_id` বা `store_slug`) সঠিকভাবে হ্যান্ডেল করতে হবে।
2. **স্প্লিট অর্ডার অপরিবর্তনীয়**: একটি অর্ডারে একাধিক স্টোরের পণ্য থাকলে চাইল্ড স্টোর অর্ডার (`store_orders`) তৈরি করা বাধ্যতামূলক।
3. **ক্যাশ অন ডেলিভারি সুরক্ষা**: সিওডি অর্ডারে ফ্রড রোধে অর্ডার প্লেসমেন্টের পর ওটিপি ভেরিফিকেশন বা কনফার্মেশন প্রটোকল সক্রিয় রাখতে হবে।
