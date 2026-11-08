---
id: DOC-AUR-062
title: Aura Bell — Frontend Architecture (Next.js & TypeScript)
type: technical
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001 (Section 11)
last_updated: 2026-11-04
---

# Aura Bell — Frontend Architecture (ফ্রন্টএন্ড আর্কিটেকচার)

## ১. ফ্রন্টএন্ড ওভারভিউ
Next.js 14+ (App Router) ব্যবহার করে প্ল্যাটফর্মের গ্রাহক ও এডমিন ইন্টারফেস নির্মিত হবে।

### প্রস্তাবিত ডিরেক্টরি কাঠামো:
```text
frontend/
├── app/
│   ├── (storefront)/             # কাস্টমার ফেসিং স্টোরফ্রন্ট
│   │   ├── best-gadget/          # Best Gadget স্টোরের পেজসমূহ
│   │   ├── aura-skin-care/       # Aura Skin Care স্টোরের পেজসমূহ
│   │   ├── cart/                 # শেয়ার্ড কার্ট পেজ
│   │   ├── checkout/             # ইউনিফাইড চেকআউট পেজ
│   │   └── account/              # কাস্টমার প্রোফাইল ও অর্ডার হিস্ট্রি
│   ├── (admin)/                  # এডমিন ব্যাকঅফিস পোর্টাল
│   │   ├── dashboard/
│   │   ├── orders/
│   │   ├── inventory/
│   │   └── reports/
│   └── api/                      # নেক্সট.জেএস বিএফএফ (BFF / Proxy) রাউটস
├── components/                   # রিইউজেবল ইউআই কম্পোনেন্টস
├── lib/                          # এপিআই ক্লায়েন্ট, ফরম্যাটার ও ইউটিলিটি
└── styles/                       # Tailwind CSS গ্লোবাল স্টাইলিং
```

---

## ২. স্টেট ম্যানেজমেন্ট ও ডেটা ফেচিং
* **Server Components**: এসইও এবং দ্রুত ফার্স্ট কন্টেন্টফুল পেইন্ট (FCP) এর জন্য প্রোডাক্ট লিস্টিং ও ক্যাটাগরি পেজ সার্ভারে রেন্ডার হবে।
* **Client State (Zustand/Context)**: শপিং কার্ট এবং ক্লায়েন্ট সেশন স্টেট লোকাল স্টোরেজ সিঙ্ক সহ হ্যান্ডেল করবে।
* **Optimistic UI**: কার্টে আইটেম বাড়ানো বা কমানোর ক্ষেত্রে অপটিমিস্টিক আপডেট হবে এবং ব্যাকএন্ডে ব্যাকগ্রাউন্ডে সিঙ্ক হবে।
