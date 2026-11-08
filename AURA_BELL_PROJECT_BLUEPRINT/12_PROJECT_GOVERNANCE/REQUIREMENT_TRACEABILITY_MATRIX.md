---
id: DOC-AUR-140
title: Aura Bell — Requirement Traceability Matrix (RTM)
type: governance
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001
last_updated: 2026-11-04
---

# Requirement Traceability Matrix (রিকোয়ারমেন্ট ট্রেসেবিলিটি ম্যাট্রিক্স)

| বিজনেস রিকোয়ারমেন্ট | প্রোডাক্ট স্পেসিফিকেশন (PRD) | সিস্টেম মডিউল | ডাটাবেজ টেবিল | টেস্ট কেস |
|---|---|---|---|---|
| `BR-AUR-001` (Multi-Store) | `PRD-STR-001` | `store` | `stores`, `store_policies` | `TC-AUR-001` |
| `BR-AUR-002` (Shared Cart) | `PRD-CHK-001` | `cart` | `carts`, `cart_items` | `TC-AUR-001` |
| `BR-AUR-003` (Split Order) | `PRD-ORD-001` | `order` | `orders`, `store_orders` | `TC-AUR-001` |
| `BR-AUR-004` (Stock Integrity)| `PRD-INV-001` | `inventory` | `inventory_balances`, `stock_movements` | `TC-AUR-002`, `TC-AUR-005` |
| `BR-AUR-005` (Financial Audit)| `PRD-PAY-001` | `payment` | `payments`, `payment_transactions` | `TC-AUR-004` |
