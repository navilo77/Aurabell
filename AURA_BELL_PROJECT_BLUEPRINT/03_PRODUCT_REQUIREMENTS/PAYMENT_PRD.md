---
id: DOC-AUR-048
title: Aura Bell — Payment Processing & Webhooks PRD
type: prd
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001
last_updated: 2026-11-04
---

# Payment & Financial PRD

## ১. উদ্দেশ্য
নিরাপদ ক্যাশ-অন-ডেলিভারি ট্র্যাকিং, অনলাইন পেমেন্ট গেটওয়ে ইন্টিগ্রেশন এবং আইডেমপোটেন্ট ওয়েবহুক প্রসেসিং নিশ্চিত করা।

## ২. ফাংশনাল স্পেসিফিকেশন
* **PRD-PAY-001 (Payment Methods)**: Cash on Delivery (COD) এবং ১টি ডিজিটাল গেটওয়ে (SSLCommerz/bKash/Shurjopay)।
* **PRD-PAY-002 (Payment Adapter Pattern)**: গেটওয়ে নিরপেক্ষ এপিআই ইন্টারফেস তৈরি যাতে ভবিষ্যতে গেটওয়ে পরিবর্তন সহজ হয়।
* **PRD-PAY-003 (Webhook Security)**: এইচএমএসি সিগনেচার বা সিক্রেট কি ভ্যালিডেশন ছাড়া কোনো ওয়েবহুক গ্রহণ না করা।
* **PRD-PAY-004 (Idempotent Execution)**: `provider_event_id` ইউনিক কনস্ট্রেইন্টের মাধ্যমে ডুপ্লিকেট ওয়েবহুক প্রসেসিং সম্পূর্ণ বন্ধ করা।
* **PRD-PAY-005 (Refund Ledger)**: গ্রাহককে কোনো টাকা ফেরত দেওয়া হলে তা `refunds` টেবিলে রেফারেন্স ও কারণসহ সংরক্ষণ করা।
