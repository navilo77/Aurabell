import { Header } from "@/components/header";
import { RoleGuard } from "@/components/role-guard";

export default function StoreAdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RoleGuard allowed={["store_manager"]}>
      <div className="min-h-screen bg-background">
        <Header title="Store Admin" />
        <main className="max-w-7xl mx-auto px-4 py-6 lg:px-8">{children}</main>
      </div>
    </RoleGuard>
  );
}
