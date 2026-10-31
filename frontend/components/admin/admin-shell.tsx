"use client";

import { BadgePercent, Bike, ClipboardList, Megaphone, Store, Tags } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

// Sections are added here as the admin area grows (orders, couriers, loyalty, reports).
const SECTIONS = [
  { href: "/admin/orders", label: "Orders", icon: ClipboardList },
  { href: "/admin/restaurants", label: "Restaurants", icon: Store },
  { href: "/admin/cuisines", label: "Cuisines", icon: Tags },
  { href: "/admin/couriers", label: "Couriers", icon: Bike },
  { href: "/admin/loyalty", label: "Loyalty", icon: BadgePercent },
  { href: "/admin/promotions", label: "Promotions", icon: Megaphone },
] as const;

/** Admin frame: section navigation (sidebar on desktop, tabs on phones) and the page. */
export function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-6 px-4 py-6 sm:px-6 lg:flex-row lg:gap-10 lg:px-8">
      <nav aria-label="Admin sections" className="lg:w-48 lg:shrink-0">
        <p className="mb-2 hidden text-xs font-semibold uppercase tracking-[0.18em] text-sage lg:block">Admin</p>
        <ul className="flex gap-1 overflow-x-auto lg:flex-col">
          {SECTIONS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <li key={href}>
                <Link
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className={`flex items-center gap-2 whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition ${
                    active ? "bg-ink text-background" : "text-ink hover:bg-surface"
                  }`}
                >
                  <Icon aria-hidden className="h-4 w-4" />
                  {label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
