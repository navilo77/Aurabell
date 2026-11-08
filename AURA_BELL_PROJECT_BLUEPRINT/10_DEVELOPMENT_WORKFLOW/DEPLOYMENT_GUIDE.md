---
id: DOC-AUR-125
title: Aura Bell — Deployment Guide & Hosting Architecture
type: workflow
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001 (Section 2, 12)
last_updated: 2026-11-04
---

# Deployment Guide (ডেপ্লয়মেন্ট নির্দেশিকা)

## ১. হোস্টিং আর্কিটেকচার
* **Frontend**: Vercel (Next.js এর জন্য অপ্টিমাইজড এজ নেটওয়ার্ক)।
* **Backend API**: Render / Railway (ডকারাইজড FastAPI কনটেইনার)।
* **Database & Auth**: Supabase Cloud Platform (Managed PostgreSQL 15+)।

## ২. ডেপ্লয়মেন্ট পাইপলাইন (CI/CD via GitHub Actions)
1. গিটহাবে পুশ হলে স্বয়ংক্রিয়ভাবে লিন্টার ও টেস্ট রান হবে।
2. টেস্ট সফল হলে স্ট্যাজিং পরিবেশে অটোমেটেড ডেপ্লয় হবে।
3. ওনার অনুমোদন সাপেক্ষে প্রোডাকশনে রিলিজ ট্যাগ পুশ হবে।
