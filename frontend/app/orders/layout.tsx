import { RequireRole } from "@/components/require-role";

export default function OrdersLayout({ children }: LayoutProps<"/orders">) {
  return <RequireRole roles={["customer"]}>{children}</RequireRole>;
}
