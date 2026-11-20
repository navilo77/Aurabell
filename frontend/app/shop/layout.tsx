import { Header } from "@/components/header";

export default function ShopLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background">
      <Header title="Marketplace" />
      <main className="max-w-7xl mx-auto px-4 py-6 lg:px-8">{children}</main>
    </div>
  );
}
