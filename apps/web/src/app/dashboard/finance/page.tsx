"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type FreeAgentInfo = {
  state: string;
  message: string;
  can_sync: boolean;
  organisation_name?: string | null;
  last_sync_at?: string | null;
};

export default function FinancePage() {
  const [tax, setTax] = useState<Record<string, unknown> | null>(null);
  const [status, setStatus] = useState<{ freeagent: FreeAgentInfo; mettle_feed: string } | null>(
    null,
  );
  const [territories, setTerritories] = useState<
    Array<{ territory_code: string; estimated_profit_gbp: number }>
  >([]);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Record<string, unknown>>("/api/v1/finance/tax-estimate", token).then(setTax).catch(() => setTax(null));
    apiGet<{ freeagent: FreeAgentInfo; mettle_feed: string }>("/api/v1/finance/status", token)
      .then(setStatus)
      .catch(() => setStatus(null));
    apiGet<Array<{ territory_code: string; estimated_profit_gbp: number }>>(
      "/api/v1/finance/profitability/territories",
      token,
    )
      .then(setTerritories)
      .catch(() => setTerritories([]));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function connectFreeAgent() {
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setSyncMsg(null);
    try {
      const { authorize_url } = await apiGet<{ authorize_url: string }>(
        "/api/v1/finance/freeagent/authorize",
        token,
      );
      window.location.href = authorize_url;
    } catch {
      setSyncMsg("Could not start FreeAgent connect — check API env credentials.");
    } finally {
      setBusy(false);
    }
  }

  async function syncFreeAgent() {
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setSyncMsg(null);
    try {
      const result = await apiPost<Record<string, string | number>>(
        "/api/v1/finance/freeagent/sync",
        {},
        token,
      );
      setSyncMsg(String(result.message ?? "Sync finished"));
      load();
    } catch {
      setSyncMsg("Sync failed — see Finance status message.");
    } finally {
      setBusy(false);
    }
  }

  const fa = status?.freeagent;

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Finance</h1>
      <p className="mt-2 text-sm text-slate-600">
        Management accounts in-app; FreeAgent is authoritative when connected. Mettle bank feed is via
        FreeAgent, not verified independently here.
      </p>

      {fa && (
        <section className="mt-6 rounded-lg border border-slate-200 bg-white p-4 text-sm">
          <h2 className="font-semibold text-slate-900">FreeAgent</h2>
          <p className="mt-1 text-slate-600">
            {fa.state} — {fa.message}
            {fa.organisation_name ? ` (${fa.organisation_name})` : null}
          </p>
          {fa.last_sync_at ? (
            <p className="mt-1 text-xs text-slate-500">Last sync: {fa.last_sync_at}</p>
          ) : null}
          <div className="mt-3 flex flex-wrap gap-2">
            {fa.state !== "connected" ? (
              <button
                type="button"
                disabled={busy}
                onClick={connectFreeAgent}
                className="rounded-md bg-emerald-800 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-900 disabled:opacity-50"
              >
                Connect FreeAgent
              </button>
            ) : (
              <button
                type="button"
                disabled={busy || !fa.can_sync}
                onClick={syncFreeAgent}
                className="rounded-md border border-emerald-800 px-4 py-2 text-xs font-semibold text-emerald-900 hover:bg-emerald-50 disabled:opacity-50"
              >
                Sync invoices
              </button>
            )}
          </div>
          {syncMsg ? <p className="mt-2 text-xs text-slate-600">{syncMsg}</p> : null}
        </section>
      )}

      {tax && (
        <section className="mt-6 rounded border p-4 text-sm">
          <h2 className="font-semibold">Tax reserve estimate ({String(tax.tax_year)})</h2>
          <p>Collected revenue: £{Number(tax.revenue_collected_gbp).toFixed(2)}</p>
          <p>Expenses: £{Number(tax.expenses_gbp).toFixed(2)}</p>
          <p>Suggested reserve: £{Number(tax.suggested_reserve_gbp).toFixed(2)}</p>
          <p className="mt-2 text-xs text-slate-500">{(tax.notes as string[])?.join(" ")}</p>
        </section>
      )}
      <section className="mt-6">
        <h2 className="font-semibold">Territory profitability (quoted contribution − expenses)</h2>
        <ul className="mt-2 text-sm">
          {territories.map((t) => (
            <li key={t.territory_code} className="border-b py-1">
              {t.territory_code} — est. profit £{t.estimated_profit_gbp.toFixed(2)}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}