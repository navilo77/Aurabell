---
id: DOC-AUR-050
title: Aura Bell — Notification & Outbox Engine PRD
type: prd
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001
last_updated: 2026-11-04
---

# Notification & Outbox Engine PRD

## ১. উদ্দেশ্য
অর্ডার নিশ্চিতকরণ, ডেলিভারি আপডেট এবং পেমেন্ট রিসিটের স্বয়ংক্রিয় ও নির্ভরযোগ্য মেসেজিং নিশ্চিত করা।

## ২. ফাংশনাল স্পেসিফিকেশন
* **PRD-NOT-001 (Transactional Outbox)**: নোটিফিকেশন ইভেন্ট সরাসরি সেন্ড না করে মূল ডাটাবেজ ট্রানজ্যাকশনের মধ্যে `outbox_events` টেবিলে সেভ করা।
* **PRD-NOT-002 (Background Dispatcher)**: ব্যাকগ্রাউন্ড ওয়ার্কার আউটবক্স টেবিল থেকে পেন্ডিং ইভেন্ট রিড করে এসএমএস ও ইমেইল প্রোভাইডারে ডেলিভারি করবে।
* **PRD-NOT-003 (Retry on Failure)**: নেটওয়ার্ক ব্যর্থতায় এক্সপোনেনশিয়াল ব্যাকঅফ সহ সর্বোচ্চ ৩ বার পুনরায় প্রেরণের চেষ্টা করা।
* **PRD-NOT-004 (Customer Notifications)**: গ্রাহক ড্যাশবোর্ডে ইন-অ্যাপ নোটিফিকেশন প্রদর্শন (`notifications` টেবিল)।
