"use client";

import Link from "next/link";
import { ArrowLeft, Compass, Sparkles } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#090b0e] text-[#f7f6f0] px-4 text-center selection:bg-gold-500/30 selection:text-gold-200">
      <div className="w-16 h-16 rounded-3xl bg-gold-500/10 border border-gold-400/30 flex items-center justify-center text-gold-300 mb-6 shadow-gold animate-pulse">
        <Compass className="w-8 h-8" />
      </div>

      <h1 className="font-serif text-6xl sm:text-7xl font-black text-gold-gradient mb-2 tracking-tight">
        404
      </h1>

      <h2 className="font-serif text-xl sm:text-2xl font-bold text-white mb-2">
        Boutique Destination Not Found
      </h2>

      <p className="text-xs sm:text-sm text-zinc-400 max-w-md mb-8 leading-relaxed">
        The boutique salon or collection page you are seeking is unavailable or has moved within the Grand Marketplace.
      </p>

      <div className="flex items-center gap-3">
        <Link
          href="/"
          className="flex items-center gap-2 px-6 py-3 rounded-full bg-gold-gradient text-black font-extrabold text-xs uppercase tracking-wider shadow-gold hover:opacity-90 transition-opacity"
        >
          <Sparkles className="w-4 h-4" />
          <span>Return Home</span>
        </Link>

        <Link
          href="/shop"
          className="flex items-center gap-2 px-6 py-3 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 text-white font-bold text-xs uppercase tracking-wider transition-colors"
        >
          <span>Explore Boutiques</span>
        </Link>
      </div>
    </div>
  );
}
