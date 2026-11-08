---
id: DOC-AUR-073
title: Aura Bell — Database Data Validation & Invariant Rules
type: database
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-DS-001, AB-DM-001
last_updated: 2026-11-04
---

# Database Data Validation Rules (ডাটাবেজ ভ্যালিডেশন ও ইনভ্যারিয়েন্টস)

পোস্টগ্রেস ডাটাবেজ স্তরে তথ্যের বিশুদ্ধতা রক্ষায় নিচের চেক কনস্ট্রেইন্টসমূহ প্রয়োগ করা হয়েছে:

1. **Non-Negative Stock Invariant**:
   - `inventory_balances.quantity_on_hand >= 0`
   - `inventory_balances.quantity_reserved >= 0`
   - কোনো পরিস্থিতিতেই রিজার্ভেশন বা স্টক শূন্যের নিচে নামতে পারবে না।
2. **Positive Pricing Invariant**:
   - `product_prices.sale_price >= 0`
   - `order_items.unit_price >= 0`
   - কোনো পণ্যের মূল্য ঋণাত্মক হতে পারবে না।
3. **Valid Quantity Invariant**:
   - `cart_items.quantity > 0`
   - `order_items.quantity > 0`
   - কার্ট বা অর্ডারে যেকোনো আইটেমের পরিমাণ অবশ্যই কমপক্ষে ১ বা তার বেশি ধনাত্মক পূর্ণসংখ্যা হতে হবে।
4. **Valid Mobile Phone Format**:
   - বাংলাদেশি ১১ ডিজিটের নম্বর ভ্যালিডেশন (`CHECK (phone ~ '^01[3-9][0-9]{8}$')`)।
