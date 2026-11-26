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

type FinanceTask = {
  title: string;
  why: string;
  when: string;
  how: string;
  professional_assistance: boolean;
  severity: string;
};

type GrowthSummary = { virtual_reserve_balance_gbp?: number; available_uncommitted_gbp?: number };

export default function FinanceHubPage() {
  const [queue, setQueue] = useState<ReviewItem[]>([]);
  const [tasks, setTasks] = useState<FinanceTask[]>([]);
  const [growth, setGrowth] = useState<GrowthSummary | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    const token = getToken();
    if (!token) return;
    apiGet<ReviewItem[]>("/api/v1/finance/bookkeeping/review-queue", token)
      .then(setQueue)
      .catch(() => setQueue([]));
    apiGet<{ tasks: FinanceTask[] }>("/api/v1/finance/insights/tasks", token)
      .then((r) => setTasks(r.tasks.slice(0, 6)))
      .catch(() => setTasks([]));
    apiGet<GrowthSummary>("/api/v1/finance/growth-fund/summary", token)
      .then(setGrowth)
      .catch(() => setGrowth(null));
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
        Plain-English bookkeeping for SurfaceCoat Ltd. FreeAgent stays the official books — here you review
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

      <section className="mt-6 rounded-xl border border-[#eab308]/30 bg-[#1a1a1a] p-4 text-white">
        <h2 className="text-sm font-semibold text-[#eab308]">SurfaceCoat Growth Fund</h2>
        <p className="mt-1 text-xs text-white/70">5% of eligible customer revenue → virtual marketing reserve (not a bank transfer).</p>
        <p className="mt-2 text-lg font-semibold">
          £{growth?.virtual_reserve_balance_gbp?.toFixed(2) ?? "—"} · available £
          {growth?.available_uncommitted_gbp?.toFixed(2) ?? "—"}
        </p>
        <a href="/dashboard/marketing/growth-fund" className="mt-2 inline-block text-xs font-semibold text-[#eab308] underline">
          Open ledger
        </a>
      </section>

      {tasks.length > 0 ? (
        <section className="mt-6 rounded-xl border border-emerald-100 bg-emerald-50/60 p-4">
          <h2 className="text-sm font-semibold text-emerald-950">What to do next</h2>
          <ul className="mt-2 space-y-2 text-sm text-slate-700">
            {tasks.map((t) => (
              <li key={t.title}>
                <span className="font-medium">{t.title}</span>
                {t.professional_assistance ? " · accountant" : null} — {t.when}
              </li>
            ))}
          </ul>
          <a href="/dashboard/tax-centre" className="mt-3 inline-block text-xs font-semibold text-emerald-800">
            Open tax centre
          </a>
        </section>
      ) : null}

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