import { RequireRole } from "@/components/require-role";

export default function AdminLayout({ children }: LayoutProps<"/admin">) {
  return <RequireRole roles={["admin"]}>{children}</RequireRole>;
}
