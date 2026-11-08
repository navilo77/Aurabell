---
id: DOC-AUR-142
title: Aura Bell — Owner Decisions Required (All Confirmed)
type: governance
status: CONFIRMED
version: 3.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, Mission Requirements, Owner Confirmation 2026-11-08
last_updated: 2026-11-08
---

# Owner Decisions Required (প্রকল্প মালিকের সিদ্ধান্তের তালিকা)

নিম্নলিখিত কৌশলগত সিদ্ধান্তগুলো **প্রকল্প মালিকের লিখিত সম্মতিসহ অনুমোদিত** হয়েছে। এগুলো এখন চূড়ান্ত এবং বাস্তবায়নের জন্য প্রস্তুত:

| সিদ্ধান্ত আইডি | বিষয়ের বিবরণ | অনুমোদিত সিদ্ধান্ত | স্থাপত্য সুপারিশ | স্থিতি | অনুমোদন তারিখ |
|---|---|---|---|---|---|
| `DEC-OWN-001` | **অনলাইন পেমেন্ট গেটওয়ে নির্বাচন** | **bKash এবং SSLCommerz (দুইটি একসাথে)** | SSLCommerz (সব কার্ড ও এমএফএস) এবং bKash ডিরেক্ট — দুটোই বাস্তবায়ন করা হবে | **CONFIRMED** | 2026-11-08 |
| `DEC-OWN-002` | **স্টক রিজার্ভেশন টাইমআউট (TTL)** | **১৫ মিনিট** | ১৫ মিনিট (গ্রাহককে পেমেন্ট শেষ করার পর্যাপ্ত সময় দেয়) | **CONFIRMED** | 2026-11-08 |
| `DEC-OWN-003` | **মাল্টি-স্টোর ডেলিভারি ফি নীতি** | **ফ্ল্যাট ডেলিভারি ফি (একই অর্ডারের জন্য একক শিপিং ফি)** | গ্রাহক কনভার্সন বৃদ্ধির জন্য একটি রিজনেবল কম্বাইন্ড ডেলিভারি ফি নির্ধারণ | **CONFIRMED** | 2026-11-08 |
| `DEC-OWN-004` | **কুরিয়ার পার্টনার নির্বাচন (V1 Manual)** | **Pathao Courier** | Pathao (ভালো সিওডি রেট ও কাভারেজ রয়েছে) | **CONFIRMED** | 2026-11-08 |

---

## Confirmed Owner Decisions (Per Mission Requirements)

The following decisions were explicitly confirmed by the project owner via mission requirements and are not pending review. They are documented here for traceability but do not carry DEC-OWN IDs as they were approved outside the formal DEC-OWN process.

| Decision | Description | Provenance | Status |
|----------|-------------|------------|--------|
| **Return Window: 7 Days** | Refund/return only within 7 days of delivery | Mission Requirements (Section: Return Policy) | **CONFIRMED** |
| **Payment Failure: Maximum 3 Failed Attempts** | Payment attempts fail after 3 retries; then release stock and mark order failed | Mission Requirements (Section: Payment Failure) | **CONFIRMED** |
| **Store-Level Shipment Fulfillment (V1)** | Parent Order splits into Store Orders; dedicated shipment per store when items originate from separate store inventories, unified under single flat delivery fee | Core Multi-Store Architecture (Section: Shipping) | **CONFIRMED** |
| **Admin Manual Refund** | All refunds require explicit admin approval | Mission Requirements (Section: Refund Policy) | **CONFIRMED** |

---

## Governance Note

- **DEC-OWN-001 through DEC-OWN-004** are **CONFIRMED** and no longer block implementation.
- **Confirmed Owner Decisions** above are implemented in documentation but do not carry DEC-OWN IDs. They are sourced from the original mission requirements and project owner communications.
- All documents referencing these decisions should cite "Confirmed Owner Decision (Mission Requirements)" or the specific DEC-OWN ID with approval date.
- All dependent documents have been updated to reflect these confirmed decisions.