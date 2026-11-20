import { Header } from "@/components/header";

export default function StoreAdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background">
      <Header title="Store Admin" />
      <main className="max-w-7xl mx-auto px-4 py-6 lg:px-8">{children}</main>
    </div>
  );
}
