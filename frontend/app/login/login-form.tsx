"use client";

import { useState } from "react";

import { FormField } from "@/components/form-field";
import { useAuth } from "@/lib/auth";
import { useAuthForm } from "@/lib/use-auth-form";

export function LoginForm() {
  const { login } = useAuth();
  const { fieldErrors, formError, submitting, submit } = useAuthForm();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  return (
    <form
      noValidate
      className="space-y-5"
      onSubmit={(event) => {
        event.preventDefault();
        void submit(() => login({ email, password }));
      }}
    >
      {formError && (
        <p role="alert" className="rounded-lg border border-accent-strong/30 bg-accent/10 px-3 py-2.5 text-sm text-accent-strong">
          {formError}
        </p>
      )}
      <FormField
        label="Email"
        type="email"
        autoComplete="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={fieldErrors.email}
      />
      <FormField
        label="Password"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={fieldErrors.password}
      />
      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-full bg-accent px-5 py-3 font-semibold text-white transition hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-60"
      >
        {submitting ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
