---
id: DOC-AUR-041
title: Aura Bell — Customer Portal & Account PRD
type: prd
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001
last_updated: 2026-11-04
---

# Customer Portal & Account PRD

## ১. উদ্দেশ্য
গ্রাহককে একটি নিরাপদ, দ্রুত এবং স্বচ্ছ ডিজিটাল একাউন্ট ও সেলফ-সার্ভিস অভিজ্ঞতা প্রদান করা।

## ২. ফাংশনাল স্পেসিফিকেশন
* **PRD-CUST-001 (Auth)**: Supabase Auth ইন্টিগ্রেশন। ফোন বা ইমেইল এবং পাসওয়ার্ডের মাধ্যমে সাইনআপ/লগইন।
* **PRD-CUST-002 (Profile)**: গ্রাহকের নাম, ফোন নম্বর, ডিফল্ট ভাষা (বাংলা/ইংরেজি) আপডেট।
* **PRD-CUST-003 (Address Book)**: একাধিক ডেলিভারি ঠিকানা যোগ, সম্পাদনা ও মোছার সুবিধা (`addresses` টেবিল)।
* **PRD-CUST-004 (Order Tracking)**: অর্ডারের রিয়েলটাইম টাইমলাইন এবং ডেলিভারি স্ট্যাটাস ট্র্যাকিং।
* **PRD-CUST-005 (Returns)**: ডেলিভারিকৃত পণ্যের জন্য ছবি ও কারণ উল্লেখ করে ৭ দিনের মধ্যে রিটার্ন রিকোয়েস্ট সাবমিট।
