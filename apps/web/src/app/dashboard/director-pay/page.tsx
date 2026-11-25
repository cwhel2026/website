"use client";

import { useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

export default function DirectorPayPage() {
  const [monthlyNet, setMonthlyNet] = useState("3000");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loan, setLoan] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);

  async function optimise() {
    const token = getToken();
    if (!token) return;
    setBusy(true);
    try {
      const r = await apiPost<Record<string, unknown>>(
        "/api/v1/finance/remuneration/optimise",
        { desired_monthly_net_gbp: Number(monthlyNet) },
        token,
      );
      setResult(r);
    } finally {
      setBusy(false);
    }
  }

  async function loadLoan() {
    const token = getToken();
    if (!token) return;
    const r = await apiGet<Record<string, unknown>>("/api/v1/finance/remuneration/directors-loan", token);
    setLoan(r);
  }

  const rec = result?.recommended as Record<string, unknown> | undefined;
  const personal = rec?.personal as Record<string, number> | undefined;

  return (
    <div className="mx-auto max-w-lg pb-16">
      <h1 className="text-xl font-semibold text-emerald-950">Director pay</h1>
      <p className="mt-2 text-sm text-slate-600">
        Enter the monthly take-home you want. The system compares salary and dividend mixes using current tax rules —
        your accountant must approve before payroll or dividends.
      </p>

      <label className="mt-4 block text-sm">
        Desired monthly take-home (£)
        <input
          type="number"
          className="mt-1 w-full rounded-lg border px-3 py-3 text-lg"
          value={monthlyNet}
          onChange={(e) => setMonthlyNet(e.target.value)}
        />
      </label>
      <button
        type="button"
        disabled={busy}
        onClick={optimise}
        className="mt-3 w-full rounded-lg bg-emerald-800 py-3 text-sm font-semibold text-white"
      >
        Calculate recommendation
      </button>

      {result?.blocked ? (
        <p className="mt-2 text-sm text-amber-800">{String(result.blocked_reason)}</p>
      ) : null}

      {rec && personal && (
        <section className="mt-5 rounded-xl border bg-white p-4 text-sm">
          <h2 className="font-semibold">Suggested mix</h2>
          <p className="mt-2 text-2xl font-semibold text-emerald-900">
            ~£{personal.monthly_take_home_gbp?.toFixed(2)}/month take-home
          </p>
          <ul className="mt-3 space-y-1 text-slate-600">
            <li>Gross salary: £{personal.salary_gross_gbp?.toFixed(2)} / year</li>
            <li>Dividends: £{personal.dividend_gbp?.toFixed(2)} / year</li>
            <li>Employer NI (est.): £{personal.employer_ni_gbp?.toFixed(2)}</li>
          </ul>
          {rec.dividend_blocked_reason ? (
            <p className="mt-2 text-xs text-red-800">{String(rec.dividend_blocked_reason)}</p>
          ) : null}
          <p className="mt-3 text-xs text-slate-500">{String(result?.plain_english)}</p>
        </section>
      )}

      <button
        type="button"
        onClick={loadLoan}
        className="mt-6 w-full rounded-lg border py-2 text-sm font-semibold"
      >
        Check director&apos;s loan balance
      </button>
      {loan ? (
        <p className="mt-2 text-sm text-slate-600">
          Balance: £{Number(loan.balance_gbp).toFixed(2)} — {String(loan.plain_english)}
        </p>
      ) : null}
    </div>
  );
}