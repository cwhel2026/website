"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Overview = {
  period_days: number;
  enquiries: number;
  quotations: number;
  revenue_collected_gbp: number;
  quoted_revenue_gbp: number;
  quote_conversion_rate: number;
};

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [regional, setRegional] = useState<{ territories: Array<{ territory_code: string; estimated_profit_gbp: number }> } | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Overview>("/api/v1/analytics/overview?days=30", token).then(setOverview).catch(() => setOverview(null));
    apiGet<{ territories: Array<{ territory_code: string; estimated_profit_gbp: number }> }>(
      "/api/v1/analytics/regional",
      token,
    )
      .then(setRegional)
      .catch(() => setRegional(null));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Analytics</h1>
      <p className="mt-2 text-sm text-slate-600">Real records only — zeros when empty.</p>
      {overview && (
        <dl className="mt-6 grid gap-3 text-sm md:grid-cols-2">
          <div className="rounded border p-3">Enquiries: {overview.enquiries}</div>
          <div className="rounded border p-3">Quotations: {overview.quotations}</div>
          <div className="rounded border p-3">
            Collected revenue: £{Number(overview.revenue_collected_gbp).toFixed(2)}
          </div>
          <div className="rounded border p-3">
            Quoted revenue: £{Number(overview.quoted_revenue_gbp).toFixed(2)}
          </div>
          <div className="rounded border p-3">Conversion (quotes/enquiries): {overview.quote_conversion_rate}%</div>
        </dl>
      )}
      {regional && (
        <section className="mt-8">
          <h2 className="font-semibold">Regional contribution (est.)</h2>
          <ul className="mt-2 text-sm">
            {regional.territories.map((t) => (
              <li key={t.territory_code}>
                {t.territory_code}: £{t.estimated_profit_gbp.toFixed(2)}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}