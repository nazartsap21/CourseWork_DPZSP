import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { AuthShell, FormSkeleton } from "@/components/auth-shell";

import { LoginForm } from "./login-form";

export const metadata: Metadata = { title: "Sign in · Forkful" };

export default function LoginPage() {
  return (
    <AuthShell
      title="Sign in"
      subtitle="Track your orders, reorder in one click and collect bonus points."
      footer={
        <>
          New to Forkful?{" "}
          <Link href="/register" className="font-semibold text-accent-strong hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      {/* The form reads ?next= via useSearchParams, which needs a Suspense boundary. */}
      <Suspense fallback={<FormSkeleton fields={2} />}>
        <LoginForm />
      </Suspense>
    </AuthShell>
  );
}
