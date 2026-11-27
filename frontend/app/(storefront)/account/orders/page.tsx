"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AccountOrdersRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/account");
  }, [router]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="w-8 h-8 rounded-full border-2 border-gold-400/20 border-t-gold-400 animate-spin" />
    </div>
  );
}
