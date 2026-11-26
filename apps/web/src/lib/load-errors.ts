"use client";

import { ApiError } from "@/lib/api-errors";

export type LoadErrorEvent = { path: string; status: number | null; message: string };

const EVENT = "sc:load-error";

export function reportLoadError(err: unknown) {
  if (typeof window === "undefined") return;
  const detail: LoadErrorEvent =
    err instanceof ApiError
      ? { path: err.path ?? "request", status: err.status, message: err.message }
      : { path: "request", status: null, message: "Could not reach the server" };
  window.dispatchEvent(new CustomEvent<LoadErrorEvent>(EVENT, { detail }));
}

/**
 * `.catch(withLoadError(() => setItems([])))` keeps the page's fallback but reports
 * the failure, so a failed request is never silently shown as "no data".
 */
export function withLoadError<T>(fallback: () => T) {
  return (err: unknown): T => {
    reportLoadError(err);
    return fallback();
  };
}

export function onLoadError(handler: (e: LoadErrorEvent) => void): () => void {
  const listener = (e: Event) => handler((e as CustomEvent<LoadErrorEvent>).detail);
  window.addEventListener(EVENT, listener);
  return () => window.removeEventListener(EVENT, listener);
}
