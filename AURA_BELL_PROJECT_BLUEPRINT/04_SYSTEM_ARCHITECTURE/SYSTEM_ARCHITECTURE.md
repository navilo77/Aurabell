---
id: DOC-AUR-060
title: Aura Bell — High-Level System Architecture Specification
type: technical
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001 (Section 1-3, 17)
last_updated: 2026-11-04
---

# Aura Bell — High-Level System Architecture (সিস্টেম আর্কিটেকচার)

## ১. আর্কিটেকচারাল সারসংক্ষেপ (Executive Summary)
Aura Bell প্ল্যাটফর্মের প্রাথমিক আর্কিটেকচার হবে একটি **Modular Monolith**। 
অপ্রয়োজনীয় জটিলতা, ডিস্ট্রিবিউটেড নেটওয়ার্ক লেটেন্সি এবং অতিরিক্ত সার্ভার খরচ পরিহার করে একক কোডবেসে সুস্পষ্ট মডিউল বাউন্ডারি দিয়ে প্ল্যাটফর্মটি তৈরি করা হয়েছে।

```mermaid
flowchart TD
    subgraph Clients["গ্রাহক ও এডমিন ক্লায়েন্ট"]
        WebCustomer["Next.js Storefront (Best Gadget / Aura Skin Care)"]
        WebAdmin["Next.js Admin Backoffice"]
    end

    subgraph BackendGateway["FastAPI ব্যাকএন্ড (Modular Monolith)"]
        API["REST API v1 (/api/v1)"]
        AuthLayer["JWT & RBAC Middleware"]
        ModuleLayer["Core Business Modules (11 Modules)"]
    end

    subgraph StorageLayer["Supabase Platform"]
        DB[("PostgreSQL 15+ Database")]
        AuthService["Supabase Auth (GoTrue)"]
        FileStore["Supabase Storage Buckets"]
    end

    subgraph Workers["ব্যাকগ্রাউন্ড ওয়ার্কার"]
        OutboxWorker["PostgreSQL Outbox Poller / Worker"]
    end

    subgraph External["বাহ্যিক সেবাসমূহ"]
        PaymentGW["Payment Gateway (bKash/SSLCommerz)"]
        CourierManual["Courier Tracking (Manual V1)"]
        SMSProvider["SMS Gateway"]
    end

    Clients --> API
    API --> AuthLayer
    AuthLayer --> ModuleLayer
    ModuleLayer --> DB
    ModuleLayer --> AuthService
    ModuleLayer --> FileStore
    DB -.-> OutboxWorker
    OutboxWorker --> SMSProvider
    ModuleLayer --> PaymentGW
```

---

## ২. প্রযুক্তিগত ভিত্তি ও দায়িত্ব বণ্টন (Approved Technology Stack)

| স্তর (Layer) | প্রযুক্তি | দায়িত্ব ও ব্যবহারের কারণ |
|---|---|---|
| **Frontend** | **Next.js (React + TypeScript)** | সার্ভার-সাইড রেন্ডারিং (SSR), এসইও ফ্রেন্ডলি স্টোরফ্রন্ট এবং দ্রুত ইন্টারফেস। |
| **Styling** | **Tailwind CSS** | মোবাইল-ফার্স্ট রেসপন্সিভ ডিজাইন ও কনসিস্টেন্ট ডিজাইন সিস্টেম। |
| **Backend** | **FastAPI (Python 3.11+)** | হাই-পারফরম্যান্স অ্যাসিঙ্ক হ্যান্ডলিং, Pydantic v2 ভ্যালিডেশন এবং অটো OpenAPI ডক। |
| **Database** | **Supabase PostgreSQL 15+** | শক্তিশালী রিলেশনাল কনস্ট্রেইন্ট, ACID ট্রানজ্যাকশন এবং Row Level Security। |
| **Auth** | **Supabase Auth** | নিরাপদ গো-ট্রু অথেনটিকেশন, পাসওয়ার্ড হ্যাশিং ও JWT ভ্যালিডেশন। |
| **Storage** | **Supabase Storage** | পণ্য ও ডকুমেন্টের ছবি নিরাপদ ক্লাউড বাকেটে সংরক্ষণ। |
| **Async Jobs** | **PostgreSQL Outbox Pattern** | কোনো কাফকা বা খরুচে মেসেজ ব্রোকার ছাড়াই ট্রানজ্যাকশনাল ইভেন্ট প্রসেসিং। |
