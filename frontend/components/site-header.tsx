"use client";

import { ShoppingBag } from "lucide-react";
import Link from "next/link";

import { useAuth } from "@/lib/auth";
import { useCart } from "@/lib/cart";

import { NotificationBell } from "./notification-bell";
import { UserMenu } from "./user-menu";

const ROLE_LINKS = {
  courier: { href: "/courier", label: "Deliveries" },
  admin: { href: "/admin", label: "Admin" },
} as const;

export function SiteHeader() {
  const { user, status } = useAuth();
  const { canOrder, itemCount } = useCart();
  const roleLink = user && user.role !== "customer" ? ROLE_LINKS[user.role] : null;

  return (
    <header className="border-b border-line bg-background">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-baseline gap-2">
          <span className="font-serif text-2xl font-semibold tracking-tight text-ink">Forkful</span>
          <span className="hidden text-xs uppercase tracking-[0.2em] text-sage sm:inline">Lviv</span>
        </Link>

        <nav className="flex items-center gap-2 sm:gap-4">
          {roleLink && (
            <Link
              href={roleLink.href}
              className="rounded-full px-3 py-1.5 text-sm font-medium text-muted-ink transition hover:bg-surface hover:text-ink"
            >
              {roleLink.label}
            </Link>
          )}

          {canOrder && (
            <Link
              href="/cart"
              aria-label={itemCount > 0 ? `Cart, ${itemCount} items` : "Cart"}
              className="relative flex h-9 w-9 items-center justify-center rounded-full text-ink transition hover:bg-surface"
            >
              <ShoppingBag aria-hidden className="h-5 w-5" />
              {itemCount > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-accent px-1 text-[0.65rem] font-semibold leading-none text-white">
                  {itemCount}
                </span>
              )}
            </Link>
          )}

          {status === "loading" && <div className="h-9 w-28 animate-pulse rounded-full bg-surface" />}

          {status === "guest" && (
            <>
              <Link href="/login" className="text-sm font-medium text-ink hover:text-accent-strong">
                Sign in
              </Link>
              <Link
                href="/register"
                className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:bg-accent-strong"
              >
                Create account
              </Link>
            </>
          )}

          {user && <NotificationBell canOpenOrders={user.role === "customer"} />}
          {user && <UserMenu user={user} />}
        </nav>
      </div>
    </header>
  );
}
