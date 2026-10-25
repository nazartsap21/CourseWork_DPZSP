import { RequireRole } from "@/components/require-role";

export default function FavoritesLayout({ children }: LayoutProps<"/favorites">) {
  return <RequireRole roles={["customer"]}>{children}</RequireRole>;
}
