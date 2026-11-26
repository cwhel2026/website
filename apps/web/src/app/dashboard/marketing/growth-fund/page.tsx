"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { MarketingCard } from "@/components/marketing-director-shell";

type LedgerResponse = {
  summary: Record<string, number | string | boolean | object>;
  entries: Array<{ type: string; amount_gbp: number; description?: string; created_at: string }>;
};

export default function GrowthFundPage() {
  const [data, setData] = useState<LedgerResponse | null>(null);
  const token = getToken();

  const load = () => {
    if (!token) return;
    apiGet<LedgerResponse>("/api/v1/finance/growth-fund/ledger", token).then(setData).catch(() => setData(null));
  };

  useEffect(load, [token]);

  async function runAlloc() {
    if (!token) return;
    await apiPost("/api/v1/finance/growth-fund/process-allocations", {}, token);
    load();
  }

  const s = data?.summary as Record<string, number> | undefined;

  return (
    <>
      <MarketingCard title="SurfaceCoat Growth Fund">
        <p className="text-xs text-slate-500">Virtual reserve — not a bank balance. Mettle pots: manual transfer only.</p>
        <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
          <div>
            <dt className="text-slate-500">Virtual balance</dt>
            <dd className="text-lg font-semibold">£{s?.virtual_reserve_balance_gbp?.toFixed(2) ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Available</dt>
            <dd className="text-lg font-semibold">£{s?.available_uncommitted_gbp?.toFixed(2) ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Committed ads</dt>
            <dd>£{s?.committed_ad_budget_gbp?.toFixed(2) ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Allocation rate</dt>
            <dd>{s?.allocation_pct ?? 5}% of eligible revenue</dd>
          </div>
        </dl>
        <button
          type="button"
          onClick={runAlloc}
          className="mt-4 w-full rounded-full bg-[#1a1a1a] py-2 text-sm text-[#eab308]"
        >
          Process new payment allocations
        </button>
      </MarketingCard>
      <ul className="space-y-2 text-sm text-white">
        {(data?.entries || []).map((e, i) => (
          <li key={i} className="rounded-lg bg-white/10 px-3 py-2">
            {e.type}: £{e.amount_gbp.toFixed(2)} — {e.description || ""}
          </li>
        ))}
      </ul>
    </>
  );
}