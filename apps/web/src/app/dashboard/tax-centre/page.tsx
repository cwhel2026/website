"use client";

import { LoadState } from "@/components/load-state";
import { gbp, pct } from "@/lib/format";
import { useApi } from "@/lib/use-api";

type Bucket = { status: string; amount_gbp: number | null; note?: string };

type Reserves = {
  recommended_reserve_gbp: number | null;
  corporation_tax: Bucket;
  vat: Bucket;
  paye: Bucket;
  has_unknown_liabilities: boolean;
  is_provisional: boolean;
  data_stale: boolean;
  sync_age_hours: number | null;
  plain_english: string;
};

type VatMonitor = {
  taxable_turnover_gbp: number;
  threshold_gbp: number;
  registration_may_be_required: boolean;
  plain_english: string;
  data_complete: boolean;
};

type Obligation = {
  slug: string;
  title: string;
  due_date: string | null;
  plain_language: string;
  why_it_matters: string;
  source_url: string | null;
};

function BucketRow({ label, bucket }: { label: string; bucket: Bucket }) {
  const known = bucket.amount_gbp !== null && bucket.amount_gbp !== undefined;
  return (
    <li className="flex flex-col gap-0.5 border-t py-2 first:border-t-0">
      <span className="flex justify-between gap-3">
        <span>{label}</span>
        <span className={known ? "font-medium text-[#1a1a1a]" : "font-medium text-amber-800"}>
          {known ? gbp(bucket.amount_gbp) : "Unknown"}
        </span>
      </span>
      {!known && bucket.note ? <span className="text-xs text-slate-500">{bucket.note}</span> : null}
    </li>
  );
}

export default function TaxCentrePage() {
  const reserves = useApi<Reserves>("/api/v1/finance/tax-centre/reserves");
  const vat = useApi<VatMonitor>("/api/v1/finance/tax-centre/vat-monitor");
  const compliance = useApi<{ obligations: Obligation[] }>("/api/v1/finance/tax-centre/compliance");

  return (
    <div className="mx-auto max-w-lg space-y-5 pb-16">
      <header>
        <h1 className="text-xl font-semibold text-[#1a1a1a]">Tax &amp; compliance</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          Planning tools for SurfaceCoat Ltd — not HMRC filing. Figures stay provisional until your accountant signs off.
        </p>
      </header>

      <section className="rounded-xl border bg-white p-4 text-sm shadow-sm">
        <h2 className="font-semibold text-[#1a1a1a]">Suggested tax reserves</h2>
        <LoadState resource={reserves}>
          {(r) => (
            <>
              {r.is_provisional ? (
                <p className="mt-1 text-xs font-medium text-amber-800">
                  Provisional — {r.data_stale ? "books not synced recently" : "books incomplete"}
                </p>
              ) : null}
              <p className="mt-2 text-2xl font-semibold text-[#1a1a1a]" data-testid="reserve-total">
                {r.recommended_reserve_gbp === null ? "Cannot be calculated yet" : gbp(r.recommended_reserve_gbp)}
              </p>
              <ul className="mt-3 text-slate-700">
                <BucketRow label="Corporation tax (est.)" bucket={r.corporation_tax} />
                <BucketRow label="VAT provision (est.)" bucket={r.vat} />
                <BucketRow label="PAYE / NI provision (est.)" bucket={r.paye} />
              </ul>
              <p className="mt-3 text-xs text-slate-600">{r.plain_english}</p>
            </>
          )}
        </LoadState>
      </section>

      <section className="rounded-xl border bg-amber-50 p-4 text-sm">
        <h2 className="font-semibold text-amber-950">VAT turnover monitor</h2>
        <LoadState resource={vat}>
          {(v) => (
            <>
              <p className="mt-2 text-[#1a1a1a]">
                Rolling 12-month taxable turnover: <strong>{gbp(v.taxable_turnover_gbp)}</strong>
              </p>
              <p className="text-slate-700">
                Threshold: {gbp(v.threshold_gbp)} ({pct(v.taxable_turnover_gbp, v.threshold_gbp)} of threshold)
              </p>
              {!v.data_complete ? (
                <p className="mt-1 text-xs text-amber-900">Based only on invoices recorded in this system.</p>
              ) : null}
              <p className="mt-2 text-slate-700">{v.plain_english}</p>
            </>
          )}
        </LoadState>
      </section>

      <section>
        <h2 className="text-sm font-semibold uppercase text-slate-500">What to do next</h2>
        <div className="mt-2">
          <LoadState
            resource={compliance}
            isEmpty={(c) => c.obligations.length === 0}
            empty="No upcoming obligations recorded."
          >
            {(c) => (
              <ul className="space-y-3">
                {c.obligations.map((ob) => (
                  <li key={ob.slug} className="rounded-xl border bg-white p-4 text-sm text-[#1a1a1a]">
                    <div className="flex justify-between gap-2">
                      <span className="font-medium">{ob.title}</span>
                      <span className="text-xs text-slate-500">{ob.due_date ?? "date needed"}</span>
                    </div>
                    <p className="mt-2 text-slate-600">{ob.plain_language}</p>
                    <p className="mt-1 text-xs text-slate-700">Why: {ob.why_it_matters}</p>
                    {ob.source_url ? (
                      <a className="mt-2 inline-block text-xs text-blue-800 underline" href={ob.source_url} target="_blank" rel="noreferrer">
                        Official guidance
                      </a>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
          </LoadState>
        </div>
      </section>
    </div>
  );
}
