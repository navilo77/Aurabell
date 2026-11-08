---
id: DOC-AUR-000
title: Aura Bell — Central Project Blueprint Readme
type: foundation
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001, AB-DM-001
last_updated: 2026-11-04
---

# Aura Bell — Central Project Blueprint (কেন্দ্রীয় প্রকল্প ব্লুপ্রিন্ট)

স্বাগতম **Aura Bell** প্রকল্পের একক ও প্রামাণ্য কেন্দ্রীয় ইঞ্জিনিয়ারিং ও আর্কিটেকচার ব্লুপ্রিন্ট হাবে।

Aura Bell হলো বাংলাদেশের বাজারের জন্য পরিকল্পিত একটি আধুনিক **Multi-Store E-commerce Platform**। এর মাধ্যমে একটি কেন্দ্রীয় ব্যাকএন্ড ও ডাটাবেজ সিস্টেমের অধীনে একাধিক স্বতন্ত্র অনলাইন স্টোর পরিচালনা করা সম্ভব। প্রাথমিক সংস্করণে (V1) দুটি ফ্ল্যাগশিপ স্টোর অন্তর্ভুক্ত রয়েছে:
1. **Best Gadget** — ইলেকট্রনিক গ্যাজেট, এক্সেসরিজ, ডিভাইস ও ওয়ারেন্টি-নিয়ন্ত্রিত পণ্য।
2. **Aura Skin Care** — স্কিন কেয়ার, বিউটি পণ্য, উপাদান (Ingredients) এবং ব্যাচ/মেয়াদ উত্তীর্ণ (Batch & Expiry) ট্র্যাকিং সংবলিত পণ্য।

---

## 🎯 প্রকল্পের মূল উদ্দেশ্য ও দর্শন

* **Shared Customer Experience**: একজন গ্রাহক একটি অ্যাকাউন্ট দিয়ে উভয় স্টোরে লগইন করতে পারবেন, উভয় স্টোরের পণ্য একই শপিং কার্টে (Shared Cart) যোগ করতে পারবেন এবং একটিমাত্র চেকআউট প্রক্রিয়ায় (Single Checkout) অর্ডার সম্পন্ন করতে পারবেন।
* **Split Order & Multi-Fulfillment**: একটি চেকআউটে একাধিক স্টোরের পণ্য থাকলে সিস্টেম স্বয়ংক্রিয়ভাবে একটি **Parent Order** এবং প্রতিটি স্টোরের জন্য পৃথক **Store Order** তৈরি করবে।
* **Modular Monolith Architecture**: অতিরিক্ত জটিল ক্লাউড ও মাইক্রোসার্ভিস পরিহার করে একটি পরিষ্কার, পরিচ্ছন্ন এবং উচ্চ কর্মক্ষমতাসম্পন্ন মডুলার মনোলিথ আর্কিটেকচার (FastAPI + Supabase PostgreSQL + Next.js)।
* **Data Integrity & Concurrency Safety**: কঠোর স্টক রিজার্ভেশন, ইমিউটেবল স্টক লেজার, ব্যাকএন্ড প্রাইস ক্যালকুলেশন এবং আইডেমপোটেন্ট পেমেন্ট প্রসেসিং।

---

## 📂 ব্লুপ্রিন্ট ফোল্ডার ডিরেক্টরি পরিচিতি

| ফোল্ডার / ফাইল | বিবরণ ও ভূমিকা |
|---|---|
| `README.md` | প্রকল্পের পরিচিতি, উদ্দেশ্য ও ব্লুপ্রিন্ট ব্যবহারের নির্দেশিকা |
| `DOCUMENT_INDEX.md` | সমস্ত ৭১টি নথির পূর্ণাঙ্গ ক্যাটালগ ও আইডি ম্যাপিং |
| `PROJECT_BRAIN.md` | এআই এজেন্ট ও ডেভেলপারদের জন্য একক প্রামাণ্য কনটেক্সট হাব (SSoT) |
| `PROJECT_STATUS.md` | প্রকল্পের বর্তমান উন্নয়ন পর্যায়, মাইলস্টোন ও স্বাস্থ্য রিপোর্ট |
| `CHANGELOG.md` | আর্কিটেকচার ও রিকোয়ারমেন্ট পরিবর্তনের সংস্করণ ইতিহাস |
| `00_FOUNDATION/` | ভিশন, বিজনেস ওভারভিউ, স্কোপ, মূলনীতি, গ্লসারি ও সীমাবদ্ধতা |
| `01_SOURCE_DOCUMENTS/` | মূল ৪টি সোর্স ডকুমেন্টের গভীর বিশ্লেষণ ও ট্র্যাকিং |
| `02_BUSINESS_REQUIREMENTS/` | বিজনেস রিকোয়ারমেন্টস, মূল বিজনেস রুলস ও স্টোর ম্যানেজমেন্ট |
| `03_PRODUCT_REQUIREMENTS/` | ১১টি বিস্তারিত প্রোডাক্ট রিকোয়ারমেন্ট ডকুমেন্ট (PRD) |
| `04_SYSTEM_ARCHITECTURE/` | মডুলার মনোলিথ আর্কিটেকচার, ব্যাকএন্ড/ফ্রন্টএন্ড/ডাটাবেজ ও ADR |
| `05_DATABASE/` | ৪৩টি টেবিলের স্কিমা, ইআরডি, রিলেশনশিপ, ভ্যালিডেশন ও মাইগ্রেশন |
| `06_API_DOCUMENTATION/` | RESTful API v1 স্পেসিফিকেশন, এন্ডপয়েন্ট, এক্সাম্পল ও এরর কোড |
| `07_UI_UX_DESIGN/` | ইউজার ফ্লো, কাস্টমার জার্নি, এডমিন ওয়ার্কফ্লো ও মোবাইল-ফার্স্ট গাইডলাইন |
| `08_SECURITY_AND_PRIVACY/` | সিকিউরিটি আর্কিটেকচার, Supabase Auth + JWT RBAC ও ডাটা প্রাইভেসি |
| `09_AI_AGENT_SYSTEM/` | মাল্টি-এজেন্ট সিস্টেম, রুলস, কোডিং স্ট্যান্ডার্ড ও Kilo Code নির্দেশনা |
| `10_DEVELOPMENT_WORKFLOW/` | ডেভেলপমেন্ট রোডম্যাপ, টাস্ক ব্রেকডাউন, গিট ওয়ার্কফ্লো ও ডেপ্লয়মেন্ট |
| `11_QUALITY_ASSURANCE/` | QA স্ট্র্যাটেজি, টেস্ট কেস, একসেপ্টেন্স ক্রাইটেরিয়া ও রিলিজ চেকলিস্ট |
| `12_PROJECT_GOVERNANCE/` | রিকোয়ারমেন্ট ট্রেসেবিলিটি ম্যাট্রিক্স (RTM), রিস্ক রেজিস্টার ও ওনার সিদ্ধান্ত |
| `13_REFERENCE/` | টেকনিক্যাল রেফারেন্স, ডিপেন্ডেন্সি ও ফিউচার রোডম্যাপ |

---

## 🛠️ প্রযুক্তি স্ট্যাক (Approved Technology Stack)

* **Frontend**: Next.js (App Router), React, TypeScript, Tailwind CSS
* **Backend**: FastAPI (Python 3.11+), Pydantic v2, SQLAlchemy 2.0 Core/ORM
* **Database**: Supabase PostgreSQL 15+ (Row Level Security - RLS)
* **Auth**: Supabase Auth (GoTrue JWT, PKCE flow)
* **Storage**: Supabase Storage (S3-compatible bucket)
* **Background Worker**: PostgreSQL-backed Transactional Outbox Pattern
* **Deployment (Target)**: Frontend on Vercel, Backend on Render/Railway, Database on Supabase

---

## 🚦 কীভাবে এই ব্লুপ্রিন্ট ব্যবহার করবেন

1. **নতুন ডেভেলপার / এআই এজেন্টের জন্য**: প্রথমে `PROJECT_BRAIN.md` এবং `09_AI_AGENT_SYSTEM/KILO_CODE_INSTRUCTIONS.md` সম্পূর্ণ পাঠ করুন।
2. **আর্কিটেকচার পর্যালোচনার জন্য**: `04_SYSTEM_ARCHITECTURE/SYSTEM_ARCHITECTURE.md` ও `05_DATABASE/DATABASE_SCHEMA.md` লক্ষ্য করুন।
3. **ফিচার ইমপ্লিমেন্টেশনের জন্য**: `03_PRODUCT_REQUIREMENTS/` ফোল্ডারের সংশ্লিষ্ট PRD এবং `10_DEVELOPMENT_WORKFLOW/TASK_BREAKDOWN.md` অনুসরণ করুন।
4. **নিয়ম ও গভর্ন্যান্স**: সিস্টেমের কোনো সিদ্ধান্ত পরিবর্তন করতে হলে `12_PROJECT_GOVERNANCE/OWNER_DECISIONS_REQUIRED.md` এবং `CHANGE_MANAGEMENT.md` মেনে ওনার অনুমোদন নিতে হবে।
