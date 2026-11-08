---
id: DOC-AUR-103
title: Aura Bell — Production Security Audit Checklist
type: security
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001 (Section 13, 14)
last_updated: 2026-11-04
---

# Production Security Checklist (প্রোডাকশন সিকিউরিটি অডিট চেকলিস্ট)

- [ ] **SSL / TLS**: সমস্ত ডোমেন ও সাবডোমেনে বৈধ HTTPS সার্টিফিকেট কার্যকর আছে।
- [ ] **No Exposed Secrets**: গিট রিপোজিটরিতে কোনো `.env` ফাইল, Supabase Service Role Key বা গেটওয়ে সিক্রেট পুশ হয়নি।
- [ ] **CORS Configuration**: নির্দিষ্ট অনুমোদিত ফ্রন্টএন্ড ডোমেন ব্যতীত ব্যাকএন্ড এপিআই-তে ওয়াইল্ডকার্ড (`*`) CORS অ্যাক্সেস বন্ধ।
- [ ] **SQL Injection Defense**: সমস্ত ডাটাবেজ কোয়ারি SQLAlchemy ORM বা প্যারামিটারাইজড স্টেটমেন্ট দিয়ে পরিচালিত।
- [ ] **Row Level Security (RLS)**: পোস্টগ্রেসের সমস্ত পাবলিক টেবিলে আরএলএস পলিসি এনফোর্স করা আছে।
- [ ] **Rate Limiting**: অথেনটিকেশন ও চেকআউট এন্ডপয়েন্টে ব্রুট-ফোর্স রোধক রেট লিমিটিং সক্রিয়।
- [ ] **Audit Logging**: রোল পরিবর্তন, রিফান্ড ও স্টক অ্যাডজাস্টমেন্ট অপারেশনে অপরিবর্তনীয় অডিট লগ জেনারেট হচ্ছে।
