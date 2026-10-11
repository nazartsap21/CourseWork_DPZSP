"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { homeForRole, useAuth } from "@/lib/auth";
import type { UserRole } from "@/types/api";

const AUDIENCE: Record<UserRole, string> = {
  customer: "customers",
  courier: "couriers",
  admin: "administrators",
};

/**
 * Client-side route guard. The JWT is in localStorage, so the server can't
 * see it and the check has to run in the browser. It only hides UI: the API
 * enforces the same roles with `roles_required`.
 */
export function RequireRole({ roles, children }: { roles: UserRole[]; children: React.ReactNode }) {
  const { user, status } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (status === "guest") {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [status, router, pathname]);

  if (status !== "authenticated" || !user) {
    return (
      <div className="mx-auto w-full max-w-6xl space-y-4 px-4 py-10 sm:px-6 lg:px-8" aria-busy>
        <div className="h-9 w-64 animate-pulse rounded-lg bg-surface" />
        <div className="h-4 w-96 max-w-full animate-pulse rounded bg-surface" />
        <div className="h-40 animate-pulse rounded-xl bg-surface" />
      </div>
    );
  }

  if (!roles.includes(user.role)) {
    return (
      <div className="mx-auto w-full max-w-xl px-4 py-16 text-center sm:px-6">
        <h1 className="font-serif text-3xl text-ink">This page is for {roles.map((r) => AUDIENCE[r]).join(" and ")}</h1>
        <p className="mt-3 text-muted-ink">You&apos;re signed in as {user.email}.</p>
        <Link
          href={homeForRole(user.role)}
          className="mt-6 inline-block rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-strong"
        >
          Go to your start page
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}
