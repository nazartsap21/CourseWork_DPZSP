import { RequireRole } from "@/components/require-role";

export default function AccountLayout({ children }: LayoutProps<"/account">) {
  return <RequireRole roles={["customer"]}>{children}</RequireRole>;
}
