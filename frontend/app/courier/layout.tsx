import { RequireRole } from "@/components/require-role";

export default function CourierLayout({ children }: LayoutProps<"/courier">) {
  return <RequireRole roles={["courier"]}>{children}</RequireRole>;
}
