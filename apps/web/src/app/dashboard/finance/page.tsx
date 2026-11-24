"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

export default function FinancePage() {
  const [tax, setTax] = useState<Record<string, unknown> | null>(null);
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [territories, setTerritories] = useState<
    Array<{ territory_code: string; estimated_profit_gbp: number }>
  >([]);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Record<string, unknown>>("/api/v1/finance/tax-estimate", token).then(setTax).catch(() => setTax(null));
    apiGet<Record<string, unknown>>("/api/v1/finance/status", token).then(setStatus).catch(() => setStatus(null));
    apiGet<Array<{ territory_code: string; estimated_profit_gbp: number }>>(
      "/api/v1/finance/profitability/territories",
      token,
    )
      .then(setTerritories)
      .catch(() => setTerritories([]));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Finance</h1>
      <p className="mt-2 text-sm text-slate-600">
        Management accounts in-app; FreeAgent authoritative when connected. Mettle via FreeAgent — not verified here.
      </p>
      {status && (
        <p className="mt-4 text-sm">
          FreeAgent: {(status.freeagent as { state: string; message: string }).state} —{" "}
          {(status.freeagent as { message: string }).message}
        </p>
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