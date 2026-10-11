import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { AuthShell, FormSkeleton } from "@/components/auth-shell";

import { RegisterForm } from "./register-form";

export const metadata: Metadata = { title: "Create account · Forkful" };

export default function RegisterPage() {
  return (
    <AuthShell
      title="Create account"
      subtitle="Every order earns bonus points toward discounts and free delivery."
      footer={
        <>
          Already have an account?{" "}
          <Link href="/login" className="font-semibold text-accent-strong hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <Suspense fallback={<FormSkeleton fields={4} />}>
        <RegisterForm />
      </Suspense>
    </AuthShell>
  );
}
