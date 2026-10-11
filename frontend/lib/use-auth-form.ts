"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError } from "./api";
import { homeForRole, safeNextPath, useAuth } from "./auth";

/**
 * Shared submit/error/redirect logic for the login and register forms.
 * The redirect happens in one place: as soon as the user becomes
 * authenticated (after submit, or when an already signed-in user opens the page).
 */
export function useAuthForm() {
  const { user } = useAuth();
  const router = useRouter();
  const nextPath = safeNextPath(useSearchParams().get("next"));
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (user) {
      router.replace(nextPath ?? homeForRole(user.role));
    }
  }, [user, nextPath, router]);

  async function submit(action: () => Promise<unknown>, fieldForCode: Record<string, string> = {}) {
    setSubmitting(true);
    setFieldErrors({});
    setFormError(null);
    try {
      await action();
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
      const field = fieldForCode[error.code];
      if (field) {
        setFieldErrors({ [field]: error.message });
      } else if (error.details.length > 0) {
        setFieldErrors(error.fieldErrors());
      } else {
        setFormError(error.message);
      }
      setSubmitting(false);
    }
  }

  return { fieldErrors, formError, submitting, submit };
}
