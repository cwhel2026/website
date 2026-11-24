"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Recommendations = {
  insights: Array<{
    territory_code: string;
    territory_name: string;
    spare_capacity_score: number;
    recommendation: string;
    suggest_advertising: boolean;
  }>;
  proposed_campaigns: Array<{
    territory_name: string;
    suggested_daily_budget_gbp: number;
    headline: string;
    rationale: string;
  }>;
};

export default function MarketingPage() {
  const [data, setData] = useState<Recommendations | null>(null);
  const [integrations, setIntegrations] = useState<Array<{ platform: string; state: string }>>([]);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Recommendations>("/api/v1/marketing/recommendations", token).then(setData).catch(() => setData(null));
    apiGet<Array<{ platform: string; state: string }>>("/api/v1/marketing/integrations", token)
      .then(setIntegrations)
      .catch(() => setIntegrations([]));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Marketing intelligence</h1>
      <p className="mt-2 text-sm text-slate-600">
        Diary-driven recommendations — no campaigns created automatically. Simulation mode default.
      </p>
      <section className="mt-6">
        <h2 className="font-semibold">Ad platform status</h2>
        <ul className="mt-2 text-sm">
          {integrations.map((i) => (
            <li key={i.platform}>
              {i.platform}: {i.state}
            </li>
          ))}
        </ul>
      </section>
      {data && (
        <>
          <section className="mt-6">
            <h2 className="font-semibold">Territory capacity</h2>
            <ul className="mt-2 space-y-2 text-sm">
              {data.insights.map((i) => (
                <li key={i.territory_code} className="rounded border px-3 py-2">
                  {i.territory_code} — {i.territory_name}: score {i.spare_capacity_score}. {i.recommendation}
                </li>
              ))}
            </ul>
          </section>
          <section className="mt-6">
            <h2 className="font-semibold">Proposed campaigns</h2>
            {data.proposed_campaigns.length === 0 ? (
              <p className="mt-2 text-sm text-slate-500">No proposals — capacity full or low spare slots.</p>
            ) : (
              <ul className="mt-2 space-y-2 text-sm">
                {data.proposed_campaigns.map((p, idx) => (
                  <li key={idx} className="rounded border border-emerald-200 bg-emerald-50/40 px-3 py-2">
                    {p.headline} — £{p.suggested_daily_budget_gbp}/day · {p.rationale}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}