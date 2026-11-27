import { Header } from "@/components/header";
import { MobileBottomBar } from "@/components/mobile-bottom-bar";
import { resolveStoreBySlug } from "@/lib/store-resolver";
import { StoreRead } from "@/lib/types";

export const dynamic = "force-dynamic";

interface StoreLayoutProps {
  children: React.ReactNode;
  params: { storeSlug: string };
}

export default async function StoreLayout({
  children,
  params,
}: StoreLayoutProps) {
  const store = await resolveStoreBySlug(params.storeSlug);

  return (
    <div className="min-h-screen bg-[#090b0e] text-[#f7f6f0] pb-20 md:pb-0">
      <Header activeTab="stores" />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16">
        {children}
      </main>
      <MobileBottomBar />
    </div>
  );
}