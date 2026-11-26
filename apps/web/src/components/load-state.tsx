"use client";

import type { ApiResource } from "@/lib/use-api";
import { describeApiError } from "@/lib/use-api";

/**
 * Renders loading / error / empty / data as distinct states. "Empty" is only shown
 * when the request succeeded and returned nothing.
 */
export function LoadState<T>({
  resource,
  isEmpty,
  empty,
  children,
}: {
  resource: ApiResource<T>;
  isEmpty?: (data: T) => boolean;
  empty?: React.ReactNode;
  children: (data: T) => React.ReactNode;
}) {
  const { data, error, loading, reload } = resource;
  if (error) {
    const { title, detail } = describeApiError(error);
    return (
      <div role="alert" className="rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900">
        <p className="font-semibold">{title}</p>
        <p className="mt-1 text-red-800">{detail}</p>
        <button
          type="button"
          onClick={reload}
          className="mt-2 rounded-full border border-red-300 px-3 py-1 text-xs font-medium text-red-900 hover:bg-red-100"
        >
          Retry
        </button>
      </div>
    );
  }
  if (loading && data === null) {
    return <p className="text-sm text-slate-500">Loading…</p>;
  }
  if (data === null) return null;
  if (isEmpty?.(data)) {
    return <div className="text-sm text-slate-600">{empty ?? "Nothing to show yet."}</div>;
  }
  return <>{children(data)}</>;
}
