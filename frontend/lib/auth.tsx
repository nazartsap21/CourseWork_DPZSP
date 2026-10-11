"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useSyncExternalStore } from "react";
import useSWR, { useSWRConfig } from "swr";

import type { AuthResponse, LoginPayload, RegisterPayload, User, UserRole } from "@/types/api";

import { ApiError, api, swrFetcher } from "./api";
import { readToken, subscribeToken, writeToken } from "./token-store";

export type AuthStatus = "loading" | "authenticated" | "guest";

interface AuthContextValue {
  user: User | null;
  status: AuthStatus;
  login: (payload: LoginPayload) => Promise<User>;
  register: (payload: RegisterPayload) => Promise<User>;
  logout: () => void;
}

const ME_KEY = "/auth/me";
const AuthContext = createContext<AuthContextValue | null>(null);

// `undefined` on the server and during hydration means "not read yet", so
// guards wait instead of redirecting a signed-in user to /login.
const getServerToken = (): string | null | undefined => undefined;

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const token = useSyncExternalStore(subscribeToken, readToken, getServerToken);
  // Global mutate: the hook-bound one targets the current key, which is null while signed out.
  const { mutate } = useSWRConfig();
  const { data: user, error } = useSWR<User, ApiError>(token ? ME_KEY : null, swrFetcher, {
    revalidateOnFocus: false,
    shouldRetryOnError: false,
  });

  // A rejected token (expired, user deleted) is dropped so the UI falls back to guest.
  useEffect(() => {
    if (error && (error.status === 401 || error.status === 404)) {
      writeToken(null);
    }
  }, [error]);

  const acceptSession = useCallback(
    async ({ access_token, user: signedIn }: AuthResponse) => {
      // Fill the cache before the token flips the SWR key on, so there's no loading flash.
      await mutate(ME_KEY, signedIn, { revalidate: false });
      writeToken(access_token);
      return signedIn;
    },
    [mutate],
  );

  const login = useCallback(
    async (payload: LoginPayload) => acceptSession(await api.post<AuthResponse>("/auth/login", payload)),
    [acceptSession],
  );

  const register = useCallback(
    async (payload: RegisterPayload) =>
      acceptSession(await api.post<AuthResponse>("/auth/register", payload)),
    [acceptSession],
  );

  const logout = useCallback(() => {
    writeToken(null);
    void mutate(ME_KEY, undefined, { revalidate: false });
  }, [mutate]);

  const value = useMemo<AuthContextValue>(() => {
    let status: AuthStatus;
    if (token === undefined) {
      status = "loading";
    } else if (token && user) {
      status = "authenticated";
    } else if (token && !error) {
      status = "loading";
    } else {
      status = "guest";
    }
    return { user: status === "authenticated" ? (user ?? null) : null, status, login, register, logout };
  }, [token, user, error, login, register, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }
  return context;
}

const ROLE_HOME: Record<UserRole, string> = {
  customer: "/",
  courier: "/courier",
  admin: "/admin",
};

export function homeForRole(role: UserRole): string {
  return ROLE_HOME[role];
}

/** Only same-site paths are allowed, so `?next=` can't redirect to another site. */
export function safeNextPath(next: string | null): string | null {
  return next && next.startsWith("/") && !next.startsWith("//") ? next : null;
}
