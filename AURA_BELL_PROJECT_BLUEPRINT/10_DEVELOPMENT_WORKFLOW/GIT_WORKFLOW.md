---
id: DOC-AUR-123
title: Aura Bell — Git Branching & Version Control Workflow
type: workflow
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001
last_updated: 2026-11-04
---

# Git Workflow & Commit Standards (গিট ব্রাঞ্চিং ও কমিট নীতি)

## ১. ব্রাঞ্চিং স্ট্র্যাটেজি
* `main`: প্রোডাকশন-রেডি স্টেবল কোড।
* `develop`: অ্যাক্টিভ ডেভেলপমেন্ট ও ইন্টিগ্রেশন ব্রাঞ্চ।
* `feature/<task-id>-<short-desc>`: নির্দিষ্ট টাস্কের ফিচার ব্রাঞ্চ (যেমন: `feature/TSK-006-stock-reservation`).
* `hotfix/<issue>`: প্রোডাকশন ইমার্জেন্সি ফিক্স।

## ২. কনভেনশনাল কমিট মেসেজ (Conventional Commits)
* `feat: add split order generation service (TSK-008)`
* `fix: correct stock reservation ttl timeout logic (TSK-006)`
* `docs: update api endpoint specification for cart (DOC-AUR-081)`
* `test: add concurrency test for checkout lock (TSK-008)`
