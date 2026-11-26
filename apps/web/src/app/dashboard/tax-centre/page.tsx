"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

export default function TaxCentrePage() {
  const [reserves, setReserves] = useState<Record<string, unknown> | null>(null);
  const [vat, setVat] = useState<Record<string, unknown> | null>(null);
  const [compliance, setCompliance] = useState<{ obligations: Array<Record<string, unknown>> } | null>(
    null,
  );

  const load = useCallback(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Record<string, unknown>>("/api/v1/finance/tax-centre/reserves", token)
      .then(setReserves)
      .catch(() => setReserves(null));
    apiGet<Record<string, unknown>>("/api/v1/finance/tax-centre/vat-monitor", token).then(setVat).catch(() => setVat(null));
    apiGet<{ obligations: Array<Record<string, unknown>> }>("/api/v1/finance/tax-centre/compliance", token)
      .then(setCompliance)
      .catch(() => setCompliance(null));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="mx-auto max-w-lg pb-16">
      <h1 className="text-xl font-semibold text-emerald-950">Tax &amp; compliance</h1>
      <p className="mt-2 text-sm leading-relaxed text-slate-600">
        Planning tools for SurfaceCoat Ltd — not HMRC filing. Figures show sources and stay provisional until your
        accountant signs off.
      </p>

      {reserves && (
        <section className="mt-5 rounded-xl border bg-white p-4 text-sm shadow-sm">
          <h2 className="font-semibold text-slate-900">Suggested tax reserves</h2>
          {reserves.is_provisional ? (
            <p className="mt-1 text-xs font-medium text-amber-800">Provisional — books incomplete or stale</p>
          ) : null}
          <p className="mt-2 text-2xl font-semibold text-emerald-900">
            £{Number(reserves.recommended_reserve_gbp).toFixed(2)}
          </p>
          <ul className="mt-3 space-y-1 text-slate-600">
            <li>Corporation tax (est.): £{Number(reserves.corporation_tax_gbp).toFixed(2)}</li>
            <li>VAT provision (est.): £{Number(reserves.vat_provision_gbp).toFixed(2)}</li>
            <li>PAYE provision (est.): £{Number(reserves.paye_provision_gbp).toFixed(2)}</li>
          </ul>
          <p className="mt-3 text-xs text-slate-500">{String(reserves.plain_english)}</p>
          <p className="mt-1 text-xs text-slate-400">{String(reserves.data_freshness)}</p>
        </section>
      )}

      {vat && (
        <section className="mt-5 rounded-xl border bg-amber-50 p-4 text-sm">
          <h2 className="font-semibold text-amber-950">VAT turnover monitor</h2>
          <p className="mt-2">
            Rolling 12-month taxable turnover: <strong>£{Number(vat.taxable_turnover_gbp).toFixed(2)}</strong>
          </p>
          <p className="text-slate-700">
            Threshold: £{Number(vat.threshold_gbp).toFixed(2)} ({Number(vat.percent_of_threshold).toFixed(1)}%)
          </p>
          <p className="mt-2 text-slate-700">{String(vat.plain_english)}</p>
        </section>
      )}

      <section className="mt-5">
        <h2 className="text-sm font-semibold uppercase text-slate-500">What to do next</h2>
        <ul className="mt-2 space-y-3">
          {(compliance?.obligations ?? []).map((ob) => (
            <li key={String(ob.slug)} className="rounded-xl border bg-white p-4 text-sm">
              <div className="flex justify-between gap-2">
                <span className="font-medium">{String(ob.title)}</span>
                <span className="text-xs text-slate-500">
                  {ob.due_date ? String(ob.due_date) : "date needed"}
                </span>
              </div>
              <p className="mt-2 text-slate-600">{String(ob.plain_language)}</p>
              <p className="mt-1 text-xs text-emerald-900">Why: {String(ob.why_it_matters)}</p>
              {ob.source_url ? (
                <a
                  className="mt-2 inline-block text-xs text-emerald-700 underline"
                  href={String(ob.source_url)}
                  target="_blank"
                  rel="noreferrer"
                >
                  Official guidance
                </a>
              ) : null}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}