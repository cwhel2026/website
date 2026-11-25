"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type ReviewItem = {
  id: string;
  confidence: number;
  category: string | null;
  explanation: string;
  personal: boolean;
  receipt_required: boolean;
  duplicate: boolean;
};

export default function FinanceHubPage() {
  const [queue, setQueue] = useState<ReviewItem[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    const token = getToken();
    if (!token) return;
    apiGet<ReviewItem[]>("/api/v1/finance/bookkeeping/review-queue", token)
      .then(setQueue)
      .catch(() => setQueue([]));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function runCategorize() {
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setStatus(null);
    try {
      const r = await apiPost<Record<string, number>>(
        "/api/v1/finance/bookkeeping/categorize/run",
        {},
        token,
      );
      setStatus(`Categorised ${r.reviewed ?? 0} lines (${r.auto_applied ?? 0} auto-applied).`);
      load();
    } catch {
      setStatus("Could not run categorisation — apply migration 0005?");
    } finally {
      setBusy(false);
    }
  }

  async function approve(id: string) {
    const token = getToken();
    if (!token) return;
    await apiPost(`/api/v1/finance/bookkeeping/review-queue/${id}/approve`, {}, token);
    load();
  }

  async function reject(id: string) {
    const token = getToken();
    if (!token) return;
    await apiPost(`/api/v1/finance/bookkeeping/review-queue/${id}/reject`, {}, token);
    load();
  }

  return (
    <div className="mx-auto max-w-lg pb-16">
      <h1 className="text-xl font-semibold text-emerald-950">Money hub</h1>
      <p className="mt-2 text-sm leading-relaxed text-slate-600">
        Plain-English bookkeeping for Revive My Drive Ltd. FreeAgent stays the official books — here you review
        suggestions and receipts. Photograph receipts in Telegram.
      </p>

      <div className="mt-4 flex flex-col gap-2 sm:flex-row">
        <button
          type="button"
          disabled={busy}
          onClick={runCategorize}
          className="w-full rounded-lg bg-emerald-800 px-4 py-3 text-sm font-semibold text-white"
        >
          Scan new bank lines
        </button>
        <a
          href="/dashboard/finance"
          className="w-full rounded-lg border border-slate-300 px-4 py-3 text-center text-sm font-semibold text-emerald-900"
        >
          FreeAgent &amp; tax
        </a>
      </div>
      {status ? <p className="mt-2 text-sm text-slate-600">{status}</p> : null}

      <section className="mt-6">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Needs your review ({queue.length})
        </h2>
        <ul className="mt-3 space-y-3">
          {queue.length === 0 ? (
            <li className="rounded-xl border bg-white p-4 text-sm text-slate-500">Nothing waiting — good work.</li>
          ) : (
            queue.map((item) => (
              <li key={item.id} className="rounded-xl border border-slate-200 bg-white p-4 text-sm shadow-sm">
                <div className="flex items-start justify-between gap-2">
                  <span className="font-medium text-slate-900">{item.category ?? "uncategorised"}</span>
                  <span className="text-xs text-slate-500">{item.confidence}% sure</span>
                </div>
                <p className="mt-2 text-slate-600">{item.explanation}</p>
                <div className="mt-2 flex flex-wrap gap-1 text-xs">
                  {item.receipt_required ? (
                    <span className="rounded bg-amber-100 px-2 py-0.5 text-amber-900">Receipt needed</span>
                  ) : null}
                  {item.personal ? (
                    <span className="rounded bg-red-100 px-2 py-0.5 text-red-900">Maybe personal</span>
                  ) : null}
                  {item.duplicate ? (
                    <span className="rounded bg-slate-200 px-2 py-0.5">Possible duplicate</span>
                  ) : null}
                </div>
                <div className="mt-3 flex gap-2">
                  <button
                    type="button"
                    onClick={() => approve(item.id)}
                    className="flex-1 rounded-lg bg-emerald-700 py-2 text-xs font-semibold text-white"
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    onClick={() => reject(item.id)}
                    className="flex-1 rounded-lg border py-2 text-xs font-semibold text-slate-700"
                  >
                    Skip
                  </button>
                </div>
              </li>
            ))
          )}
        </ul>
      </section>
    </div>
  );
}