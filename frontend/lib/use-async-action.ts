"use client";

import { useState } from "react";

import { ApiError } from "./api";

/** Runs one API action at a time and keeps its errors: field errors for forms, a message otherwise. */
export function useAsyncAction() {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  async function run<T>(action: () => Promise<T>): Promise<T | undefined> {
    setPending(true);
    setError(null);
    setFieldErrors({});
    try {
      return await action();
    } catch (err) {
      if (!(err instanceof ApiError)) throw err;
      if (err.details.length > 0) setFieldErrors(err.fieldErrors());
      setError(err.message);
      return undefined;
    } finally {
      setPending(false);
    }
  }

  return { run, pending, error, fieldErrors, setError };
}
