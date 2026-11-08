---
id: DOC-AUR-049
title: Aura Bell — Shipping, Delivery & Couriers PRD
type: prd
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001
last_updated: 2026-11-04
---

# Shipping & Delivery PRD

## ১. উদ্দেশ্য
স্টোরভিত্তিক পণ্যের প্যাকেজিং, কুরিয়ারে হস্তান্তর এবং ডেলিভারি জীবনচক্র স্বচ্ছভাবে পরিচালনা করা।

## ২. ফাংশনাল স্পেসিফিকেশন
* **PRD-SHP-001 (Multi-Shipment Architecture)**: বিভিন্ন স্টোরের পণ্য বা ওয়্যারহাউসের পার্থক্যের কারণে একটি প্যারেন্ট অর্ডারের একাধিক `shipments` তৈরি হতে পারে।
* **PRD-SHP-002 (Manual Courier Dispatch - V1)**: এডমিন প্যানেল থেকে কুরিয়ারের নাম (Steadfast, Pathao, RedX ইত্যাদি) নির্বাচন ও ট্র্যাকিং কোড ইনপুট প্রদান।
* **PRD-SHP-003 (Shipment State Lifecycle)**: `PENDING` ➡️ `BOOKED` ➡️ `PICKED_UP` ➡️ `IN_TRANSIT` ➡️ `DELIVERED` / `RETURNED` পরিচালনা।
* **PRD-SHP-004 (Tracking Events)**: প্রতিটি ডেলিভারি স্ট্যাটাস পরিবর্তনের টাইমস্ট্যাম্প `shipment_events` টেবিলে রেকর্ড করা।
