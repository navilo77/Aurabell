---
id: DOC-AUR-095
title: Aura Bell — Mobile-First Responsive Guidelines
type: design
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001
last_updated: 2026-11-04
---

# Mobile-First Responsive Guidelines (মোবাইল-ফার্স্ট গাইডলাইন)

## ১. প্রেক্ষাপট
বাংলাদেশে ই-কমার্স ট্রাফিকের ৮০% এর বেশি স্মার্টফোন ব্রাউজার থেকে আসে। অতএব ডেস্কটপ নয়, বরং মোবাইল স্ক্রিনই Aura Bell-এর প্রাথমিক ডিজাইন বেঞ্চমার্ক।

## ২. মোবাইল ডিজাইনের আবশ্যিক নিয়মাবলী
* **Thumb Zone Optimization**: মূল অ্যাকশন বাটন (Add to Cart, Checkout) স্ক্রিনের নিচের অংশে ফিক্সড বটম বারে থাকতে হবে যাতে একহাতে সহজে ট্যাপ করা যায়।
* **Touch Target Size**: সমস্ত ক্লিকেবল বাটন ও আইকনের ন্যূনতম সাইজ হতে হবে `48x48 px`।
* **Input Form Zoom Prevention**: মোবাইল ব্রাউজারে ইনপুট ফিল্ডে ফোকাস করলে অটো-জুম ঠেকাতে ফন্ট সাইজ কমপক্ষে `16px` হতে হবে।
* **Low Bandwidth Optimization**: বাংলাদেশের 4G/3G নেটওয়ার্কে দ্রুত লোডিংয়ের জন্য ইমেজগুলোকে Next.js অপটিমাইজেশন দিয়ে WebP/AVIF ফরম্যাটে ডেলিভার করতে হবে।
