"use client";

import { useSyncExternalStore } from "react";

const noopSubscribe = () => () => {};

/**
 * False during server render and hydration, true afterwards. Lets pages that
 * depend on localStorage show a skeleton instead of flashing an empty state.
 */
export function useHydrated(): boolean {
  return useSyncExternalStore(
    noopSubscribe,
    () => true,
    () => false,
  );
}
