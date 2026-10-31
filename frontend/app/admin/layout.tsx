import { AdminShell } from "@/components/admin/admin-shell";
import { RequireRole } from "@/components/require-role";

export default function AdminLayout({ children }: LayoutProps<"/admin">) {
  return (
    <RequireRole roles={["admin"]}>
      <AdminShell>{children}</AdminShell>
    </RequireRole>
  );
}
