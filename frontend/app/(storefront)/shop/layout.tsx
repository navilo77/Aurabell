import { Header } from "@/components/header";
import { MobileBottomBar } from "@/components/mobile-bottom-bar";

export default function ShopLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#090b0e] text-[#f7f6f0] pb-20 md:pb-0">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16">{children}</main>
      <MobileBottomBar />
    </div>
  );
}
