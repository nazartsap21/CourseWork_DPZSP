"use client";

import { useState } from "react";

import { FormField } from "@/components/form-field";
import { useAuth } from "@/lib/auth";
import { useAuthForm } from "@/lib/use-auth-form";

export function RegisterForm() {
  const { register } = useAuth();
  const { fieldErrors, formError, submitting, submit } = useAuthForm();
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "" });

  const update = (field: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement>) =>
    setForm((current) => ({ ...current, [field]: event.target.value }));

  return (
    <form
      noValidate
      className="space-y-5"
      onSubmit={(event) => {
        event.preventDefault();
        void submit(() => register({ ...form, phone: form.phone || undefined }), { EMAIL_TAKEN: "email" });
      }}
    >
      {formError && (
        <p role="alert" className="rounded-lg border border-accent-strong/30 bg-accent/10 px-3 py-2.5 text-sm text-accent-strong">
          {formError}
        </p>
      )}
      <FormField label="Name" autoComplete="name" value={form.name} onChange={update("name")} error={fieldErrors.name} />
      <FormField
        label="Email"
        type="email"
        autoComplete="email"
        value={form.email}
        onChange={update("email")}
        error={fieldErrors.email}
      />
      <FormField
        label="Phone"
        type="tel"
        autoComplete="tel"
        placeholder="+380"
        hint="Optional. The courier calls this number if they can't find you."
        value={form.phone}
        onChange={update("phone")}
        error={fieldErrors.phone}
      />
      <FormField
        label="Password"
        type="password"
        autoComplete="new-password"
        hint="At least 8 characters."
        value={form.password}
        onChange={update("password")}
        error={fieldErrors.password}
      />
      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-full bg-accent px-5 py-3 font-semibold text-white transition hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-60"
      >
        {submitting ? "Creating account…" : "Create account"}
      </button>
    </form>
  );
}
