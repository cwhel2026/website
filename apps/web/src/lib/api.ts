import { ApiError, parseApiError } from "@/lib/api-errors";
import { getCsrfToken } from "@/lib/auth-client";

/** Same-origin when NEXT_PUBLIC_API_URL is unset (combined Railway deploy). */
export function resolveApiUrl(): string {
  const configured = (process.env.NEXT_PUBLIC_API_URL ?? "").trim().replace(/\/$/, "");
  if (configured && typeof window !== "undefined") {
    const origin = window.location.origin.replace(/\/$/, "");
    if (configured === origin) {
      return "";
    }
  }
  if (configured) return configured;
  if (typeof window !== "undefined") return "";
  return (process.env.API_INTERNAL_URL ?? "http://localhost:8000").replace(/\/$/, "");
}

type Method = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

/**
 * Authenticated by the HttpOnly session cookie. The historical `token` argument on the
 * exported helpers is accepted for call-site compatibility and deliberately ignored.
 */
async function request<T>(method: Method, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET") {
    const csrf = getCsrfToken();
    if (csrf) headers["X-CSRF-Token"] = csrf;
  }
  const res = await fetch(`${resolveApiUrl()}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
    credentials: "same-origin",
  });
  if (!res.ok) {
    const detail = await res.text();
    const err = parseApiError(res.status, detail);
    err.path = path;
    throw err;
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

/* eslint-disable @typescript-eslint/no-unused-vars */
export function apiGet<T>(path: string, _token?: string | null): Promise<T> {
  return request<T>("GET", path);
}

export function apiPost<T>(path: string, body: unknown, _token?: string | null): Promise<T> {
  return request<T>("POST", path, body);
}

export function apiPut<T>(path: string, body: unknown, _token?: string | null): Promise<T> {
  return request<T>("PUT", path, body);
}

export function apiPatch<T>(path: string, body: unknown, _token?: string | null): Promise<T> {
  return request<T>("PATCH", path, body);
}

export function apiDelete<T>(path: string, _token?: string | null): Promise<T> {
  return request<T>("DELETE", path);
}
/* eslint-enable @typescript-eslint/no-unused-vars */

export { ApiError };

/** @deprecated use resolveApiUrl() — empty on combined same-origin deploys */
export const API_URL = resolveApiUrl();
