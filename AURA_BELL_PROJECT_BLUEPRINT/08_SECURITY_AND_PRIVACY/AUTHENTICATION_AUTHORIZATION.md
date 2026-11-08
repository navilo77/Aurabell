---
id: DOC-AUR-101
title: Aura Bell — Authentication & RBAC Authorization Specification
type: security
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001 (Section 10), AB-DS-001 (Section 4)
last_updated: 2026-11-04
---

# Authentication & RBAC Specification (অথেনটিকেশন ও আরব্যাক)

## ১. অথেনটিকেশন আর্কিটেকচার
* প্ল্যাটফর্মটি ইউজার সাইনআপ, ওটিপি এবং পাসওয়ার্ড ম্যানেজমেন্টের জন্য **Supabase Auth** ব্যবহার করে।
* সফল অথেনটিকেশনে ক্লায়েন্ট একটি ক্রিপ্টোগ্রাফিক GoTrue JWT টোকেন লাভ করে।
* FastAPI ব্যাকএন্ড প্রতিটি এপিআই রিকোয়েস্টে হেডার থেকে JWT ডিকোড করে সিগনেচার, ইস্যুয়ার (`iss`) এবং মেয়াদ (`exp`) যাচাই করে।

---

## ২. রোল-বেসড এক্সেস কন্ট্রোল (RBAC Matrix)

| রোল (Role) | ক্যাটালগ ভিউ | কার্ট ও অর্ডার প্লেস | এডমিন ড্যাশবোর্ড | ইনভেন্টরি অ্যাডজাস্ট | পেমেন্ট ও রিফান্ড |
|---|:---:|:---:|:---:|:---:|:---:|
| **Anonymous / Public** | ✅ | ✅ (Guest Cart)| ❌ | ❌ | ❌ |
| **Customer** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Support Agent** | ✅ | ❌ | ✅ (Read Only) | ❌ | ❌ |
| **Inventory Manager** | ✅ | ❌ | ✅ | ✅ | ❌ |
| **Store Manager** | ✅ | ❌ | ✅ | ✅ | ❌ |
| **Super Admin / Owner** | ✅ | ✅ | ✅ | ✅ | ✅ |
