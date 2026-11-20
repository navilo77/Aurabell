"use client";

import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background text-foreground">
      <h1 className="text-6xl font-bold text-primary mb-4">404</h1>
      <p className="text-xl font-semibold mb-2">পৃষ্ঠা পাওয়া যায়নি</p>
      <p className="text-muted-foreground mb-6">
        আপনি যে পেজটি খুঁজছেন তা এখানে নেই।
      </p>
      <Link
        href="/shop"
        className="px-6 py-3 rounded-md bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors"
      >
        শপে ফিরে যান
      </Link>
    </div>
  );
}
