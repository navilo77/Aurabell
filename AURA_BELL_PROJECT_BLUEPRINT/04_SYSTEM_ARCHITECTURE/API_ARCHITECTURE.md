---
id: DOC-AUR-065
title: Aura Bell — API Architecture & Versioning Strategy
type: technical
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001 (Section 5)
last_updated: 2026-11-04
---

# Aura Bell — API Architecture & Versioning (এপিআই আর্কিটেকচার)

## ১. এপিআই নিয়মাবলী ও রুট ডিজাইন
* সমস্ত এপিআই প্রমিত RESTful কনভেনশন এবং ইউআরএল পাথ ভার্সনিং অনুসরণ করবে।
* **Base Path**: `/api/v1`
* সমস্ত রিকোয়েস্ট ও রেসপন্স বডি স্ট্যান্ডার্ড `application/json` ফরম্যাটে আদান-প্রদান হবে।

## ২. অথেনটিকেশন ও টোকেন পাসিং
* সিকিউরড এন্ডপয়েন্টগুলোতে `Authorization: Bearer <JWT_TOKEN>` হেডার পাঠানো বাধ্যতামূলক।
* FastAPI ব্যাকএন্ড মিডলওয়্যার প্রতি রিকোয়েস্টে টোকেন সিগনেচার, এক্সপায়ারি ও ইউজার রোল পরীক্ষা করবে।
