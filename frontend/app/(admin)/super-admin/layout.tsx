import { Header } from "@/components/header";
import { RoleGuard } from "@/components/role-guard";

export default function SuperAdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RoleGuard allowed={["owner", "admin", "super_admin"]}>
      <div className="min-h-screen bg-background">
        <Header title="Super Admin" />
        <main className="max-w-7xl mx-auto px-4 py-6 lg:px-8">{children}</main>
      </div>
    </RoleGuard>
  );
}