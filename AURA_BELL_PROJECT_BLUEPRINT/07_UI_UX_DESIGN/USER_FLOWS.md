---
id: DOC-AUR-090
title: Aura Bell — End-to-End User Flows Specification
type: design
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001
last_updated: 2026-11-04
---

# Aura Bell — End-to-End User Flows (ব্যবহারকারী প্রবাহ)

```mermaid
flowchart TD
    Start([গ্রাহকের আগমন]) --> Browse[পণ্য ব্রাউজিং / সার্চ]
    Browse --> Select[ভ্যারিয়েন্ট নির্বাচন: সাইজ/কালার]
    Select --> AddCart[Add to Cart]
    AddCart --> ViewCart[শেয়ার্ড কার্ট পর্যবেক্ষণ]
    ViewCart --> AuthCheck{লগইন আছেন কি?}
    AuthCheck -- না --> Login[দ্রুত ফোন/ইমেইল লগইন বা OTP]
    Login --> Checkout
    AuthCheck -- হ্যাঁ --> Checkout[চেকআউট স্ক্রিন]
    Checkout --> AddressSelect[ডেলিভারি ঠিকানা নির্বাচন]
    AddressSelect --> PaySelect{পেমেন্ট নির্বাচন}
    PaySelect -- ক্যাশ-অন-ডেলিভারি --> PlaceOrder[অর্ডার প্লেস করুন]
    PaySelect -- অনলাইন পেমেন্ট --> Gateway[গেটওয়ে পেমেন্ট সম্পন্ন]
    Gateway --> PlaceOrder
    PlaceOrder --> Split[ব্যাকএন্ড: প্যারেন্ট ও স্টোর অর্ডার তৈরি]
    Split --> Success([সফল অর্ডার নিশ্চিতকরন পেজ])
```

## 6. 3D মল এক্সপিরিয়েন্সের হ্যান্ডলিং
* **3D মল থেকে এন্ট্রি:** `Start` নোড থেকে নতুন ব্রাঞ্চ যোগ করা:
    `Start --> 3D_Mall_Entry[3D মল এন্ট্রি করুন (স্বেচ্ছাসেবিক)]`
* **3D মল নেভিগেশন:** 3D মল এন্ট্রিতে প্রবেশ করলে:
    `3D_Mall_Entry --> 3D_Environment[3D ভার্চুয়াল মল পরিবেশ]
    3D_Environment --> Enter_Store[যে কোনো স্টোর এন্ট্রি এপ্রোচ করুন]
    Enter_Store --> 3D_To_2D_Transition[3D থেকে 2D স্টোরফ্রন্টে ট্রানজিশন]
    3D_To_2D_Transition --> Success([2D স্টোরফ্রন্টে অবতরণ])`
* **3D বিকল্প:** 2D স্টোরিং বিকল্পটি বেছে নিলে:
    `Start --> 2D_Shopping[2D শপিং পছন্দ করুন]
    2D_Shopping --> Browse[পণ্য ব্রাউজিং / সার্চ]
    Browse --> Select[ভ্যারিয়েন্ট নির্বাচন: সাইজ/কালার]
    Select --> AddCart[Add to Cart]
    AddCart --> ViewCart[শেয়ার্ড কার্ট পর্যবেক্ষণ]`
* **মোবাইল সেটিংস:** মোবাইল ডিভাইসে 3D মল এক্সপেরিয়েন্স:
    `3D_Environment --> Mobile_3D_Controls[মোবাইল জয়স্টিক + টাচ কন্ট্রোল]
    Mobile_3D_Controls --> Enter_Store[এপ্রোচ করা যায়]`
