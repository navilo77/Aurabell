import { Suspense } from "react";
import { SearchPageClient } from "./search-client";

export default function SearchPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-10 h-10 rounded-full border-2 border-gold-400/20 border-t-gold-400 animate-spin" />
      </div>
    }>
      <SearchPageClient />
    </Suspense>
  );
}