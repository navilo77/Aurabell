---
id: DOC-AUR-004
title: Aura Bell — Project Changelog
type: governance
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001, AB-DM-001
last_updated: 2026-11-04
---

# Aura Bell — Project Changelog (পরিবর্তন ও সংস্করণের ইতিহাস)

এই নথিতে Aura Bell ব্লুপ্রিন্ট ও সিস্টেম স্পেসিফিকেশনের সমস্ত পরিবর্তন, সংযোজন এবং সিদ্ধান্তের সংস্করণ ট্র্যাকিং লিপিবদ্ধ করা হয়।

---

## [1.1.0] — 2026-11-08

### Added (সংযোজিত)
* **Owner Decisions Confirmed**: All four blocking decisions approved by project owner:
  - DEC-OWN-001: Payment Gateway Selection — bKash and SSLCommerz (both implemented)
  - DEC-OWN-002: Stock Reservation TTL — 15 minutes
  - DEC-OWN-003: Delivery Fee Policy — Flat fee per order
  - DEC-OWN-004: Courier Partner Selection — Pathao Courier
* **Implementation Unblocked**: All payment, inventory, shipping, and checkout modules now ready for implementation
* **Documentation Updates**: All dependent specifications updated with confirmed decision values
* **V1 Classification Updated**: All payment, inventory, shipping specs reclassified from 'Future/Specified' to 'V1 READY'

### Changed (পরিবর্তিত)
* OWNER_DECISIONS_REQUIRED.md v3.0: All DEC-OWN decisions status updated to CONFIRMED with approval date
* OPEN_OWNER_DECISIONS.md v2.0: All decisions marked CONFIRMED with approved values
* PAYMENT_SYSTEM_ARCHITECTURE.md v2.0: All DEC-OWN references updated, status CONFIRMED
* PAYMENT_PROVIDER_INTERFACE.md v2.0: Gateway selection confirmed (bKash + SSLCommerz)
* PAYMENT_PROVIDER_ADAPTER.md v2.0: Adapter implementation unblocked
* PAYMENT_WEBHOOK_LIFECYCLE.md v2.0: TTL and gateway configs confirmed
* PAYMENT_RECONCILIATION.md v2.0: Gateway access confirmed (bKash + SSLCommerz)
* PAYMENT_TIMEOUT_FAILURE.md v2.0: TTL set to 15 minutes
* PAYMENT_REFUND_MANUAL.md v2.0: Gateway refund APIs accessible
* INVENTORY_SYSTEM_ARCHITECTURE.md v2.0: TTL set to 15 minutes
* SHIPPING_SYSTEM_ARCHITECTURE.md v2.0: Courier (Pathao) and fee policy (flat) confirmed, invalid RULE-AUR refs fixed
* CART_CHECKOUT_PRD.md: Delivery fee calculation updated to flat fee policy
* PROJECT_STATUS.md: Milestone MS-1.8 unblocked, all decisions confirmed
* DOCUMENT_INDEX.md: OWNER_DECISIONS_REQUIRED.md status updated to CONFIRMED
* DOCUMENT_APPROVAL_STATUS.md: OWNER_DECISIONS_REQUIRED.md status updated to CONFIRMED

---

## [1.0.0] — 2026-11-04

### Added (সংযোজিত)
* **কেন্দ্রীয় ব্লুপ্রিন্ট হাব প্রতিষ্ঠা**: সম্পূর্ণ একক ফোল্ডার `AURA_BELL_PROJECT_BLUEPRINT/` তৈরি এবং সমস্ত ডকুমেন্টের স্ট্যান্ডার্ডাইজেশন।
* **সোর্স ডকুমেন্ট সমন্বয়**: গুগল ড্রাইভে সংরক্ষিত ৪টি মূল টেকনিক্যাল ও বিজনেস ডকুমেন্ট বিশ্লেষণ করে পূর্ণাঙ্গ রিপোর্ট তৈরি (`01_SOURCE_DOCUMENTS/`):
  - `AB-PV-001` (Aura Bell — Project Vision)
  - `AB-SA-001` (Aura Bell — System Architecture)
  - `AB-DS-001` (Aura Bell — Database Schema)
  - `AB-DM-001` (Aura Bell — Database SQL Migrations v1)
* **প্রোডাক্ট রিকোয়ারমেন্ট ডকুমেন্টস (PRDs)**: কাস্টমার, এডমিন, স্টোর, ক্যাটালগ, ইনভেন্টরি, কার্ট/চেকআউট, অর্ডার, পেমেন্ট, শিপিং এবং নোটিফিকেশন মডিউলের জন্য ১১টি স্বয়ংসম্পূর্ণ PRD তৈরি।
* **সিস্টেম আর্কিটেকচার স্পেসিফিকেশন**: মডুলার মনোলিথ আর্কিটেকচার, ১১টি ব্যাকএন্ড মডিউল বাউন্ডারি, Next.js ফ্রন্টএন্ড আর্কিটেকচার, পোস্টগ্রেস ডাটাবেজ স্ট্রাকচার এবং ১০টি আর্কিটেকচারাল ডিসিশন রেকর্ড (ADR-001 থেকে ADR-010)।
* **সম্পূর্ণ ডাটাবেজ স্কিমা**: ৪৩টি রিলেশনাল টেবিল, টাইপ কনস্ট্রেইন্ট, পোস্টগ্রেস এনামস, ইউইউআইডি প্রাইমারি কি, অটোমেটেড টাইমস্ট্যাম্প ট্রিগার এবং আরএলএস স্ট্র্যাটেজি।
* **এপিআই স্পেসিফিকেশন**: RESTful API v1 এর বিশদ এন্ডপয়েন্ট ক্যাটালগ, অথেনটিকেশন মেকানিজম, এরর কোডস এবং পেলোড এক্সাম্পল।
* **ইউআই/ইউএক্স ও সিকিউরিটি গাইডলাইনস**: কাস্টমার জার্নি, এডমিন ওয়ার্কফ্লো, ডিজাইন সিস্টেম, মোবাইল-ফার্স্ট গাইডলাইন এবং কমপ্রিহেনসিভ সিকিউরিটি আর্কিটেকচার।
* **এআই এজেন্ট নির্দেশনা ফ্রেমওয়ার্ক**: Kilo Code নির্দেশাবলী, এজেন্ট রোলস, কোডিং স্ট্যান্ডার্ডস এবং ডকুমেন্টেশন আপডেট রুলস।
* **গভর্ন্যান্স ও ট্রেসেবিলিটি**: রিকোয়ারমেন্ট ট্রেসেবিলিটি ম্যাট্রিক্স (RTM), রিস্ক রেজিস্টার ও ওনার ডিসিশন রেজিস্টার।

