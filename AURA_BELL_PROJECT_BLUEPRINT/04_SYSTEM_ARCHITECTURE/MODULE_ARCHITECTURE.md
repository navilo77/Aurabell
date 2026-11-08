---
id: DOC-AUR-061
title: Aura Bell — Backend Module Architecture & Boundaries
type: technical
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001 (Section 4)
last_updated: 2026-11-04
---

# Aura Bell — Backend Module Architecture (মডিউল আর্কিটেকচার)

FastAPI ব্যাকএন্ডটি মনোলিথ হলেও কোডবেসটি অভ্যন্তরীণভাবে ১১টি স্বতন্ত্র বিজনেস মডিউলে বিভক্ত থাকবে। কোনো মডিউল অন্য মডিউলের টেবিল সরাসরি কোয়ারি বা পরিবর্তন করতে পারবে না; শুধুমাত্র পাবলিক সার্ভিস মেথড বা ইভেন্টের মাধ্যমে যোগাযোগ হবে।

## ১১টি ব্যাকএন্ড মডিউল:

1. **Identity Module (`app.modules.identity`)**:
   - দায়িত্ব: ইউজার প্রোফাইল, রোলস (`roles`), পারমিশনস (`permissions`), ইউজার রোল ম্যাপিং ও ঠিকানা বুক।
2. **Store Module (`app.modules.store`)**:
   - দায়িত্ব: স্টোর ক্রিয়েশন, স্টোর সেটিংস, ব্র্যান্ডিং ও নিজস্ব টার্মস/রিটার্ন পলিসি (`store_policies`)।
3. **Catalog Module (`app.modules.catalog`)**:
   - দায়িত্ব: ক্যাটাগরি হায়ারার্কি, প্রোডাক্টস, ভ্যারিয়েন্টস, ইমেজ ও বিশেষ অ্যাট্রিবিউটস (Warranty/Expiry/Batch)।
4. **Pricing Module (`app.modules.pricing`)**:
   - দায়িত্ব: সার্ভার-সাইড প্রাইস ক্যালকুলেশন, ডিসকাউন্ট ভ্যালিডেশন ও কার্ট টোটাল ভেরিফিকেশন।
5. **Inventory Module (`app.modules.inventory`)**:
   - দায়িত্ব: রিয়েলটাইম স্টক ব্যালেন্স (`inventory_balances`), অ্যাটমিক রিজার্ভেশন এবং ইমিউটেবল স্টক লেজার (`stock_movements`)।
6. **Cart Module (`app.modules.cart`)**:
   - দায়িত্ব: শেয়ার্ড শপিং কার্ট সেশন, আইটেম যোগ/বিয়োগ এবং মাল্টি-স্টোর কার্ট ভ্যালিডেশন।
7. **Order Module (`app.modules.order`)**:
   - দায়িত্ব: প্যারেন্ট অর্ডার তৈরি, স্টোরভিত্তিক স্প্লিট অর্ডার জেনারেশন এবং অর্ডার আইটেম স্ন্যাপশট সংরক্ষণ।
8. **Payment Module (`app.modules.payment`)**:
   - দায়িত্ব: সিওডি অর্ডার ট্র্যাকিং, অনলাইন পেমেন্ট এডাপ্টার এবং ক্রিপ্টোগ্রাফিক ওয়েবহুক সিগনেচার যাচাই।
9. **Fulfillment Module (`app.modules.fulfillment`)**:
   - দায়িত্ব: কুরিয়ার বুকিং, শিপমেন্ট ক্রিয়েশন, ট্র্যাকিং কোড এসাইন ও ডেলিভারি ইভেন্ট ট্র্যাকিং।
10. **Return & Support Module (`app.modules.support`)**:
    - দায়িত্ব: রিটার্ন রিকোয়েস্ট যাচাই, অনুমোদন, রিফান্ড ইনিশিয়েশন ও গ্রাহক সাপোর্ট টিকেট ম্যানেজমেন্ট।
11. **Reporting Module (`app.modules.reporting`)**:
    - দায়িত্ব: দৈনিক বিক্রয় ক্যাশ সামারি (`daily_reports`), ইনভেন্টরি মুভমেন্ট অডিট ও প্রফিট মার্জিন রিপোর্ট।
