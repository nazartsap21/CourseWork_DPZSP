"use client";

import { ChevronDown, LogOut, UserRound } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useRef, useState } from "react";

import { useAuth } from "@/lib/auth";
import { useDismiss } from "@/lib/use-dismiss";
import type { User } from "@/types/api";

const ROLE_LABEL: Record<User["role"], string> = {
  customer: "Customer",
  courier: "Courier",
  admin: "Administrator",
};

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export function UserMenu({ user }: { user: User }) {
  const { logout } = useAuth();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const closeMenu = useCallback(() => setOpen(false), []);
  const containerRef = useRef<HTMLDivElement>(null);

  useDismiss(containerRef, open, closeMenu);

  const signOut = () => {
    setOpen(false);
    logout();
    router.push("/");
  };

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-haspopup="menu"
        className="flex items-center gap-2 rounded-full border border-line bg-card py-1 pl-1 pr-3 text-sm text-ink transition hover:border-muted-ink/40"
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-sage text-xs font-semibold text-white">
          {initials(user.name)}
        </span>
        <span className="hidden max-w-32 truncate sm:inline">{user.name.split(" ")[0]}</span>
        <ChevronDown aria-hidden className="h-4 w-4 text-muted-ink" />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 z-20 mt-2 w-60 overflow-hidden rounded-xl border border-line bg-card shadow-[0_12px_32px_rgba(34,25,22,0.12)]"
        >
          <div className="border-b border-line px-4 py-3">
            <p className="truncate text-sm font-semibold text-ink">{user.name}</p>
            <p className="truncate text-xs text-muted-ink">{user.email}</p>
            <p className="mt-1 text-xs uppercase tracking-wider text-sage">{ROLE_LABEL[user.role]}</p>
          </div>
          {user.role === "customer" && (
            <Link
              href="/account"
              role="menuitem"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2 px-4 py-2.5 text-sm text-ink hover:bg-surface"
            >
              <UserRound aria-hidden className="h-4 w-4 text-muted-ink" />
              My account
            </Link>
          )}
          <button
            type="button"
            role="menuitem"
            onClick={signOut}
            className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm text-ink hover:bg-surface"
          >
            <LogOut aria-hidden className="h-4 w-4 text-muted-ink" />
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}
