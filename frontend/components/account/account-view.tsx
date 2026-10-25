"use client";

import { Heart, Receipt } from "lucide-react";
import Link from "next/link";
import { Suspense, useState } from "react";
import { useSWRConfig } from "swr";

import { FormField } from "@/components/form-field";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { User } from "@/types/api";

import { LoyaltySection } from "./loyalty-section";

/** Submit state for a small form: field errors from the API, a general error, a "saved" flag. */
function useFormSubmit() {
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [saved, setSaved] = useState(false);

  async function submit(action: () => Promise<unknown>): Promise<boolean> {
    setSubmitting(true);
    setSaved(false);
    setFieldErrors({});
    setFormError(null);
    try {
      await action();
      setSaved(true);
      return true;
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
      if (error.details.length > 0) setFieldErrors(error.fieldErrors());
      else setFormError(error.message);
      return false;
    } finally {
      setSubmitting(false);
    }
  }

  return { fieldErrors, formError, submitting, saved, submit };
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="border-t border-line pt-8">
      <h2 className="font-serif text-2xl text-ink">{title}</h2>
      <div className="mt-5">{children}</div>
    </section>
  );
}

function SubmitRow({ submitting, saved, label }: { submitting: boolean; saved: boolean; label: string }) {
  return (
    <div className="flex items-center gap-4">
      <button
        type="submit"
        disabled={submitting}
        className="rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-strong disabled:opacity-50"
      >
        {submitting ? "Saving…" : label}
      </button>
      {saved && (
        <span role="status" className="text-sm text-sage">
          Saved
        </span>
      )}
    </div>
  );
}

function ProfileForm({ user }: { user: User }) {
  const { mutate } = useSWRConfig();
  const [name, setName] = useState(user.name);
  const [phone, setPhone] = useState(user.phone ?? "");
  const form = useFormSubmit();

  return (
    <form
      noValidate
      className="max-w-lg space-y-5"
      onSubmit={(event) => {
        event.preventDefault();
        void form.submit(async () => {
          const updated = await api.patch<User>("/auth/me", { name, phone: phone || null });
          // The header and every useAuth() consumer read this cache entry.
          await mutate("/auth/me", updated, { revalidate: false });
        });
      }}
    >
      {form.formError && (
        <p role="alert" className="text-sm text-accent-strong">
          {form.formError}
        </p>
      )}
      <FormField label="Email" value={user.email} disabled hint="The email is your login and can't be changed." />
      <FormField label="Name" autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} error={form.fieldErrors.name} />
      <FormField
        label="Phone"
        type="tel"
        autoComplete="tel"
        placeholder="+380"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        error={form.fieldErrors.phone}
        hint="The courier calls this number if they can't find you."
      />
      <SubmitRow submitting={form.submitting} saved={form.saved} label="Save profile" />
    </form>
  );
}

function PasswordForm() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const form = useFormSubmit();

  return (
    <form
      noValidate
      className="max-w-lg space-y-5"
      onSubmit={(event) => {
        event.preventDefault();
        void form
          .submit(() => api.post("/auth/me/password", { current_password: current, new_password: next }))
          .then((ok) => {
            if (ok) {
              setCurrent("");
              setNext("");
            }
          });
      }}
    >
      {form.formError && (
        <p role="alert" className="text-sm text-accent-strong">
          {form.formError}
        </p>
      )}
      <FormField
        label="Current password"
        type="password"
        autoComplete="current-password"
        value={current}
        onChange={(e) => setCurrent(e.target.value)}
        error={form.fieldErrors.current_password}
      />
      <FormField
        label="New password"
        type="password"
        autoComplete="new-password"
        value={next}
        onChange={(e) => setNext(e.target.value)}
        error={form.fieldErrors.new_password}
        hint="At least 8 characters."
      />
      <SubmitRow submitting={form.submitting} saved={form.saved} label="Change password" />
    </form>
  );
}

export function AccountView() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 pb-16 pt-8 sm:px-6">
      <h1 className="font-serif text-4xl tracking-tight text-ink">Account</h1>
      <p className="mt-1 text-muted-ink">{user.email}</p>

      <nav aria-label="Account sections" className="mt-6 flex flex-wrap gap-3">
        <Link
          href="/orders"
          className="inline-flex items-center gap-2 rounded-full border border-line bg-card px-4 py-2 text-sm font-medium text-ink hover:border-muted-ink/50"
        >
          <Receipt aria-hidden className="h-4 w-4 text-sage" />
          My orders
        </Link>
        <Link
          href="/favorites"
          className="inline-flex items-center gap-2 rounded-full border border-line bg-card px-4 py-2 text-sm font-medium text-ink hover:border-muted-ink/50"
        >
          <Heart aria-hidden className="h-4 w-4 text-sage" />
          Favorites
        </Link>
      </nav>

      <div className="mt-10 space-y-10">
        <Section title="Bonus points and card">
          {/* Reads ?premium=cancelled with useSearchParams, which needs Suspense. */}
          <Suspense fallback={<div className="h-48 animate-pulse rounded-xl bg-surface" />}>
            <LoyaltySection />
          </Suspense>
        </Section>
        <Section title="Profile">
          {/* Keyed by user so the form resets if a different account signs in. */}
          <ProfileForm key={user.id} user={user} />
        </Section>
        <Section title="Password">
          <PasswordForm />
        </Section>
      </div>
    </main>
  );
}
