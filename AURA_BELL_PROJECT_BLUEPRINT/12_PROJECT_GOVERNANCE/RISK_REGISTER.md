---
id: DOC-AUR-141
title: Aura Bell — Project Risk Register & Mitigation Matrix
type: governance
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001
last_updated: 2026-11-04
---

# Project Risk Register (ঝুঁকি নিরূপণ ও প্রশমন রেজিস্টার)

| ঝুঁকি আইডি | সম্ভাব্য ঝুঁকি ও প্রভাব | তীব্রতা | প্রশমন কৌশল (Mitigation Strategy) |
|---|---|---|---|
| `RSK-AUR-001` | ফ্ল্যাশ সেলে একই পণ্যের শেষ স্টকে বহু গ্রাহকের একসাথে অর্ডার চেষ্টা। | High | ডাটাবেজে `SELECT FOR UPDATE` রো-লকিং এবং নন-নেগেটিভ চেক কনস্ট্রেইন্ট ব্যবহার। |
| `RSK-AUR-002` | সিওডি অর্ডারে গ্রাহকের পণ্য রিসিভ করতে অস্বীকৃতি (Return to Origin)। | High | অর্ডার প্লেসের পর ফোন ওটিপি বা অটো-কনফার্মেশন কল ভেরিফিকেশন ব্যবস্থা রাখা। |
| `RSK-AUR-003` | পেমেন্ট গেটওয়ের নেটওয়ার্ক টাইমআউট বা ডুপ্লিকেট ওয়েবহুক কল। | Medium | ক্রিপ্টোগ্রাফিক সিগনেচার যাচাই ও `provider_event_id` ইউনিক কনস্ট্রেইন্ট। |
| `RSK-AUR-004` | ক্লায়েন্ট সাইড থেকে ম্যানিপুলেটেড প্রাইস পাঠানো। | High | ফ্রন্টএন্ড প্রাইস সম্পূর্ণ উপেক্ষা করে ব্যাকএন্ড সার্ভারে লাইভ প্রাইস পুনরায় হিসাব করা। |
