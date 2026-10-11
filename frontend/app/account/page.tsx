"use client";

import { useAuth } from "@/lib/auth";

export default function AccountPage() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6 lg:px-8">
      <h1 className="font-serif text-4xl tracking-tight text-ink">My account</h1>
      <dl className="mt-8 grid max-w-lg grid-cols-[8rem_1fr] gap-y-3 text-sm">
        <dt className="text-muted-ink">Name</dt>
        <dd className="text-ink">{user.name}</dd>
        <dt className="text-muted-ink">Email</dt>
        <dd className="text-ink">{user.email}</dd>
        <dt className="text-muted-ink">Phone</dt>
        <dd className="text-ink">{user.phone ?? "Not set"}</dd>
      </dl>
    </main>
  );
}
