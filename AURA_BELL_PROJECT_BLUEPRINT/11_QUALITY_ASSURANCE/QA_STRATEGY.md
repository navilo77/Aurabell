---
id: DOC-AUR-130
title: Aura Bell — Quality Assurance Strategy & Quality Gates
type: qa
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001 (Section 15)
last_updated: 2026-11-04
---

# Quality Assurance Strategy (কোয়ালিটি এসিউরেন্স স্ট্র্যাটেজি)

## ১. কোয়ালিটি গেটস (Quality Gates)
* **Gate 1 (Static Analysis)**: কোডে কোনো টাইপস্ক্রিপ্ট টাইপ এরর বা পাইথন টাইপ এরর (Mypy) থাকা চলবে না।
* **Gate 2 (Unit Testing)**: সমস্ত কোর বিজনেস ক্যালকুলেশন (Price, Discount, Tax, Stock Balance) ১০০% টেস্ট কভারেজ থাকতে হবে।
* **Gate 3 (Security Check)**: কোডে কোনো হার্ডকোডেড সিক্রেট বা অরক্ষিত এন্ডপয়েন্ট থাকা চলবে না।
* **Gate 4 (Regression Prevention)**: নতুন ফিচারের কারণে বিদ্যমান কোনো টেস্ট ব্যর্থ হতে পারবে না।
