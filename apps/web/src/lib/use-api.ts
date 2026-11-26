"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { ApiError } from "@/lib/api-errors";

export type ApiResource<T> = {
  data: T | null;
  error: Error | null;
  loading: boolean;
  reload: () => void;
};

/** GET a resource and keep failures visible instead of collapsing them into "empty". */
export function useApi<T>(path: string | null): ApiResource<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState<boolean>(Boolean(path));
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (!path) return;
    let cancelled = false;
    setLoading(true);
    apiGet<T>(path)
      .then((d) => {
        if (cancelled) return;
        setData(d);
        setError(null);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(e instanceof Error ? e : new Error(String(e)));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [path, nonce]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);
  return { data, error, loading, reload };
}

export function describeApiError(error: Error): { title: string; detail: string } {
  if (error instanceof ApiError) {
    if (error.status === 401) return { title: "Signed out", detail: "Your session has ended. Sign in again." };
    if (error.status === 403) {
      return {
        title: "Not permitted",
        detail: "This account cannot perform that action (read-only accounts can view but not change data).",
      };
    }
    if (error.status === 404) return { title: "Not available", detail: "This feature is not available on this deployment." };
    if (error.status === 503) return { title: "Service unavailable", detail: error.message };
    if (error.status >= 500) {
      return { title: "Server error", detail: `The server failed to load this (HTTP ${error.status}). It has been logged.` };
    }
    return { title: `Request failed (HTTP ${error.status})`, detail: error.message };
  }
  return { title: "Could not reach the server", detail: "Check your connection and try again." };
}
