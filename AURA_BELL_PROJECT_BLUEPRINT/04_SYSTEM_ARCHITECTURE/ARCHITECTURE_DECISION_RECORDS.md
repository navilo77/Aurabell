---
id: DOC-AUR-066
title: Aura Bell — Architectural Decision Records (ADRs)
type: technical
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001
last_updated: 2026-11-04
---

# Aura Bell — Architectural Decision Records (ADRs)

| ADR ID | সিদ্ধান্ত শিরোনাম | স্থিতি | নির্বাচিত বিকল্প ও কারণ |
|---|---|---|---|
| `ADR-001` | **Modular Monolith over Microservices** | Confirmed | প্রারম্ভিক জটিলতা ও খরচ কমিয়ে দ্রুত ডেলিভারি নিশ্চিত করতে মডুলার মনোলিথ নির্বাচন। |
| `ADR-002` | **FastAPI over Django/Flask** | Confirmed | দ্রুত অ্যাসিঙ্ক প্রসেসিং, Pydantic টাইপ সেফটি ও বিল্ট-ইন OpenAPI ডকুমেন্টেশন। |
| `ADR-003` | **Supabase PostgreSQL & Auth** | Confirmed | প্রোডাকশন গ্রেড পোস্টগ্রেস, গো-ট্রু অথেনটিকেশন এবং শক্তিশালী সিকিউরিটি ও RLS সুবিধা। |
| `ADR-004` | **Next.js App Router for Frontend** | Confirmed | সার্ভার সাইড রেন্ডারিং (SSR) দিয়ে এসইও অপটিমাইজেশন এবং ইউনিফাইড ফুল-স্ট্যাক ফ্রন্টএন্ড। |
| `ADR-005` | **Transactional Outbox for Messaging** | Confirmed | কাফকা বা খরুচে ব্রোকার পরিহার করে ডাটাবেজ ভিত্তিক নির্ভরযোগ্য ইভেন্ট ও নোটিফিকেশন ডেলিভারি। |
| `ADR-006` | **Immutable Stock Ledger Pattern** | Confirmed | সমস্ত স্টক পরিবর্তন `stock_movements` টেবিলে সংরক্ষিত থাকবে যাতে শতভাগ অডিট ট্রেইল থাকে। |
| `ADR-007` | **Split Order Architecture** | Confirmed | ১টি প্যারেন্ট অর্ডার ও স্টোরভিত্তিক চাইল্ড অর্ডার দিয়ে ভিন্ন ব্র্যান্ড ফুলফিলমেন্ট সহজ করা। |
| `ADR-008` | **Server-Side Price Recalculation** | Confirmed | ফ্রন্টএন্ড টেম্পারিং প্রতিরোধে চেকআউটের সময় ব্যাকএন্ড ডাটাবেজ থেকে দাম পুনর্বিবেচনা করবে। |
| `ADR-009` | **Payment Gateway Adapter Pattern** | Confirmed | ভবিষ্যতে গেটওয়ে পরিবর্তনের সুবিধার্থে ইন্টারফেস-ভিত্তিক এডাপ্টার আর্কিটেকচার। |
| `ADR-010` | **Manual Courier Dispatch for V1** | Confirmed | প্রারম্ভিক স্থিতিশীলতার জন্য V1-এ ম্যানুয়াল ট্র্যাকিং এন্ট্রি এবং ফেজ ২-এ এপিআই ইন্টিগ্রেশন। |
