"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Campaign = {
  id: string;
  name: string;
  platform: string;
  status: string;
  simulation_only: boolean;
  daily_budget_gbp: number;
};

export default function AdvertisingPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);

  function reload() {
    const token = getToken();
    if (!token) return;
    apiGet<Campaign[]>("/api/v1/marketing/campaigns", token).then(setCampaigns).catch(() => setCampaigns([]));
  }

  useEffect(reload, []);

  async function createSample() {
    const token = getToken();
    if (!token) return;
    await apiPost(
      "/api/v1/marketing/campaigns",
      {
        name: "Blackpool tarmac test",
        platform: "meta",
        service_slug: "tarmac-driveway-restoration",
        daily_budget_gbp: 15,
        monthly_budget_gbp: 200,
        simulation_only: true,
        headline: "Restore your driveway — Blackpool",
      },
      token,
    );
    reload();
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Advertising</h1>
      <p className="mt-2 text-sm text-slate-600">
        Launch requires approval. No fictional spend — connect Meta in Marketing → Integrations.
      </p>
      <button
        type="button"
        onClick={createSample}
        className="mt-4 rounded-full border border-slate-300 px-4 py-2 text-sm text-slate-600"
      >
        Create internal draft (simulation only)
      </button>
      <ul className="mt-6 space-y-2 text-sm">
        {campaigns.map((c) => (
          <li key={c.id} className="rounded border px-3 py-2">
            {c.name} · {c.platform} · {c.status} · £{c.daily_budget_gbp}/day
            {c.simulation_only ? " · simulation" : ""}
          </li>
        ))}
      </ul>
    </div>
  );
}