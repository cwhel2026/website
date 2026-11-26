"use client";

import { useState } from "react";
import { LoadState } from "@/components/load-state";
import { apiPost } from "@/lib/api";
import { gbp } from "@/lib/format";
import { describeApiError, useApi } from "@/lib/use-api";

type Recommended = {
  salary_gross_gbp: number;
  dividend_gbp: number;
  annual_take_home_gbp: number;
  monthly_take_home_gbp: number;
  personal_tax_gbp: number;
  employer_ni_gbp: number;
  corporation_tax_gbp: number;
  lawful_dividend: boolean;
  target_gap_gbp?: number;
  dividend_blocked_reason?: string;
};

type OptimiseResult = {
  blocked?: boolean;
  blocked_reason?: string;
  recommended?: Recommended;
  plain_english?: string;
};

type Loan = { balance_gbp: number | null; plain_english: string };

export default function DirectorPayPage() {
  const [monthlyNet, setMonthlyNet] = useState("3000");
  const [result, setResult] = useState<OptimiseResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const loan = useApi<Loan>("/api/v1/finance/remuneration/directors-loan");

  async function optimise() {
    const desired = Number(monthlyNet);
    if (!Number.isFinite(desired) || desired <= 0) {
      setError("Enter a monthly amount greater than zero.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      setResult(
        await apiPost<OptimiseResult>("/api/v1/finance/remuneration/optimise", { desired_monthly_net_gbp: desired }),
      );
    } catch (e) {
      setResult(null);
      setError(describeApiError(e as Error).detail);
    } finally {
      setBusy(false);
    }
  }

  const rec = result?.recommended;

  return (
    <div className="mx-auto max-w-lg pb-16">
      <h1 className="text-xl font-semibold text-[#1a1a1a]">Director pay</h1>
      <p className="mt-2 text-sm text-slate-600">
        Enter the monthly take-home you want. The system compares salary and dividend mixes using current tax rules —
        your accountant must approve before payroll or dividends. Calculating saves nothing.
      </p>

      <label className="mt-4 block text-sm text-[#1a1a1a]">
        Desired monthly take-home (£)
        <input
          type="number"
          min="1"
          className="mt-1 w-full rounded-lg border px-3 py-3 text-lg"
          value={monthlyNet}
          onChange={(e) => setMonthlyNet(e.target.value)}
        />
      </label>
      <button
        type="button"
        disabled={busy}
        onClick={optimise}
        className="mt-3 w-full rounded-lg bg-[#1a1a1a] py-3 text-sm font-semibold text-white disabled:opacity-60"
      >
        {busy ? "Calculating…" : "Calculate recommendation"}
      </button>

      {error ? (
        <p role="alert" className="mt-3 rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-900">
          {error}
        </p>
      ) : null}

      {result?.blocked ? (
        <div className="mt-4 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950" data-testid="pay-blocked">
          <p className="font-semibold">No recommendation yet</p>
          <p className="mt-1">{result.blocked_reason}</p>
        </div>
      ) : null}

      {rec && !result?.blocked ? (
        <section className="mt-5 rounded-xl border bg-white p-4 text-sm text-[#1a1a1a]">
          <h2 className="font-semibold">Suggested mix</h2>
          <p className="mt-2 text-2xl font-semibold">~{gbp(rec.monthly_take_home_gbp)}/month take-home</p>
          <ul className="mt-3 space-y-1 text-slate-700">
            <li>Gross salary: {gbp(rec.salary_gross_gbp)} / year</li>
            <li>Dividends: {gbp(rec.dividend_gbp)} / year</li>
            <li>Personal tax (est.): {gbp(rec.personal_tax_gbp)} / year</li>
            <li>Employer NI (est.): {gbp(rec.employer_ni_gbp)} / year</li>
          </ul>
          {rec.dividend_blocked_reason ? <p className="mt-2 text-xs text-red-800">{rec.dividend_blocked_reason}</p> : null}
          {result?.plain_english ? <p className="mt-3 text-xs text-slate-600">{result.plain_english}</p> : null}
        </section>
      ) : null}

      <section className="mt-6 rounded-xl border bg-white p-4 text-sm text-[#1a1a1a]">
        <h2 className="font-semibold">Director&apos;s loan</h2>
        <LoadState resource={loan}>
          {(l) => (
            <p className="mt-1 text-slate-700">
              Balance: {gbp(l.balance_gbp)} — {l.plain_english}
            </p>
          )}
        </LoadState>
      </section>
    </div>
  );
}
