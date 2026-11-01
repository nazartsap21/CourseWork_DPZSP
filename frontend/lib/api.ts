import type { ApiErrorBody, ApiFieldError } from "@/types/api";

import { readToken } from "./token-store";

// Relative base: next.config rewrites /api/* to Flask, so no CORS is needed.
const API_BASE = "/api/v1";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly details: ApiFieldError[] = [],
  ) {
    super(message);
    this.name = "ApiError";
  }

  /** Field-level messages keyed by field name, for inline form errors. */
  fieldErrors(): Record<string, string> {
    return Object.fromEntries(this.details.map((d) => [d.field, d.message]));
  }
}

function isErrorBody(value: unknown): value is ApiErrorBody {
  if (typeof value !== "object" || value === null || !("error" in value)) {
    return false;
  }
  const error = (value as { error: unknown }).error;
  return typeof error === "object" && error !== null && "code" in error && "message" in error;
}

async function send(method: string, path: string, body?: unknown, accept = "application/json"): Promise<Response> {
  const headers: Record<string, string> = { Accept: accept };
  const token = readToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "Can't reach the server. Check your connection.");
  }
  if (!response.ok) {
    const data: unknown = await response.json().catch(() => null);
    if (isErrorBody(data)) {
      const { code, message, details } = data.error;
      throw new ApiError(response.status, code, message, details);
    }
    throw new ApiError(response.status, "UNKNOWN_ERROR", "Something went wrong. Try again.");
  }
  return response;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const response = await send(method, path, body);
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body),
  patch: <T>(path: string, body?: unknown) => request<T>("PATCH", path, body),
  delete: <T = void>(path: string) => request<T>("DELETE", path),
  /** A file response (e.g. a CSV report); a plain link can't send the JWT header. */
  download: async (path: string) => (await send("GET", path, undefined, "*/*")).blob(),
};

/** Default SWR fetcher: the SWR key is the API path. */
export const swrFetcher = <T>(path: string) => api.get<T>(path);
