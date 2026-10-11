import { RequireRole } from "@/components/require-role";

export default function CheckoutLayout({ children }: LayoutProps<"/checkout">) {
  return <RequireRole roles={["customer"]}>{children}</RequireRole>;
}
