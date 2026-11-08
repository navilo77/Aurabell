---
id: DOC-AUR-133
title: Aura Bell — Production Release Readiness Checklist
type: qa
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001 (Section 14)
last_updated: 2026-11-04
---

# Production Release Readiness Checklist (প্রোডাকশন রিলিজ চেকলিস্ট)

- [ ] ডাটাবেজের সমস্ত ৪৩টি টেবিল, ফরেন কি এবং ট্রিগার প্রোডাকশন পোস্টগ্রেসে মাইগ্রেট করা হয়েছে।
- [ ] প্রাথমিক দুটি স্টোর (`best-gadget` এবং `aura-skin-care`) এবং ডিফল্ট ওয়্যারহাউস সিড করা হয়েছে।
- [ ] Supabase Auth ইমেইল/এসএমএস টেমপ্লেট ব্র্যান্ডিং সমন্বয় করা হয়েছে।
- [ ] পেমেন্ট গেটওয়ের লাইভ প্রোডাকশন ক্রেডেনশিয়াল ও ওয়েবহুক ইউআরএল সফলভাবে টেস্ট করা হয়েছে।
- [ ] এন্ড-টু-এন্ড পারচেজ ফ্লো টেস্ট সম্পন্ন হয়েছে।
- [ ] ব্যাকগ্রাউন্ড আউটবক্স ওয়ার্কার অবিচ্ছিন্নভাবে সচল আছে।
