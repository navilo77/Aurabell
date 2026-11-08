---
id: DOC-AUR-081
title: Aura Bell — Complete API Endpoints Catalog
type: technical
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001 (Section 5)
last_updated: 2026-11-04
---

# Aura Bell — Complete API Endpoints Catalog (এন্ডপয়েন্ট তালিকা)

| মডিউল | মেথড | এন্ডপয়েন্ট | বিবরণ | অথেনটিকেশন |
|---|---|---|---|---|
| **Auth & Me** | `GET` | `/api/v1/me` | বর্তমান ইউজারের পরিচয় ও রোলস | Customer / Admin |
| | `GET` | `/api/v1/me/profile` | ইউজার প্রোফাইল বিবরণ | Customer / Admin |
| | `PATCH` | `/api/v1/me/profile` | নাম, ফোন বা ভাষা আপডেট | Customer / Admin |
| | `GET` | `/api/v1/me/addresses` | সেভ করা ডেলিভারি ঠিকানা তালিকা | Customer |
| | `POST` | `/api/v1/me/addresses` | নতুন ডেলিভারি ঠিকানা যোগ | Customer |
| | `PATCH` | `/api/v1/me/addresses/{id}` | ঠিকানা পরিবর্তন | Customer |
| | `DELETE` | `/api/v1/me/addresses/{id}`| ঠিকানা মোছা | Customer |
| **Stores** | `GET` | `/api/v1/stores` | সক্রিয় স্টোরসমূহের তালিকা | Public |
| | `GET` | `/api/v1/stores/{slug}` | নির্দিষ্ট স্টোরের বিস্তারিত ও পলিসি | Public |
| | `GET` | `/api/v1/stores/{slug}/categories` | স্টোরের ক্যাটাগরি তালিকা | Public |
| **Catalog** | `GET` | `/api/v1/products` | ফিল্টার ও পেজিনেশনসহ প্রোডাক্ট তালিকা | Public |
| | `GET` | `/api/v1/products/{id}` | প্রোডাক্ট ভ্যারিয়েন্ট, স্টক ও বিবরণ | Public |
| | `GET` | `/api/v1/categories` | সমস্ত পাবলিক ক্যাটাগরি ট্রি | Public |
| **Cart** | `GET` | `/api/v1/cart` | বর্তমান ব্যবহারকারীর শেয়ার্ড কার্ট | Session / Customer |
| | `POST` | `/api/v1/cart/items` | কার্টে নতুন আইটেম যুক্ত করা | Session / Customer |
| | `PATCH` | `/api/v1/cart/items/{id}`| কার্টের আইটেমের পরিমাণ আপডেট | Session / Customer |
| | `DELETE` | `/api/v1/cart/items/{id}`| কার্ট থেকে আইটেম রিমুভ | Session / Customer |
| **Checkout**| `POST`| `/api/v1/checkout` | কার্ট ভ্যালিডেশন, প্রাইস ক্যালকুলেশন ও অর্ডার প্লেস | Customer |
| **Orders** | `GET` | `/api/v1/orders` | গ্রাহকের অর্ডার তালিকা | Customer |
| | `GET` | `/api/v1/orders/{id}` | অর্ডারের বিস্তারিত টাইমলাইন ও আইটেমস | Customer |
| | `POST` | `/api/v1/orders/{id}/cancel` | পেন্ডিং অর্ডার বাতিলের অনুরোধ | Customer |
| **Payment** | `POST` | `/api/v1/payments` | পেমেন্ট ইনিশিয়েট ও গেটওয়ে ইউআরএল জেনারেশন | Customer |
| | `GET` | `/api/v1/payments/{id}` | পেমেন্টের বর্তমান স্ট্যাটাস যাচাই | Customer / Admin |
| | `POST` | `/api/v1/webhooks/payments/{provider}` | গেটওয়ে ওয়েবহুক লিসেনার | Public (HMAC Verified) |
| **Admin** | `GET` | `/api/v1/admin/dashboard` | সেলস, অর্ডার ও ইনভেন্টরি ড্যাশবোর্ড | Admin |
| | `GET` | `/api/v1/admin/orders` | ব্যাকঅফিস অর্ডার ম্যানেজমেন্ট | Admin |
| | `PATCH` | `/api/v1/admin/orders/{id}/status` | অর্ডার স্ট্যাটাস ম্যানুয়াল আপডেট | Admin |
| | `GET` | `/api/v1/admin/inventory` | ইনভেন্টরি ব্যালেন্স ও ওয়্যারহাউস ভিউ | Admin |
| | `POST` | `/api/v1/admin/inventory/adjust` | ফিজিক্যাল স্টক অ্যাডজাস্টমেন্ট এন্ট্রি | Admin |
