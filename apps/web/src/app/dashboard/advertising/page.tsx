"use client";

import { LoadState } from "@/components/load-state";
import { SimulatedBadge } from "@/components/simulated-badge";
import { useApi } from "@/lib/use-api";

type Campaign = {
  id: string;
  name: string;
  platform: string;
  status: string;
  simulation_only: boolean;
  daily_budget_gbp: number;
};

export default function AdvertisingPage() {
  const campaigns = useApi<Campaign[]>("/api/v1/marketing/campaigns");

  return (
    <div>
      <h1 className="text-2xl font-semibold text-[#1a1a1a]">Advertising</h1>
      <p className="mt-2 text-sm text-slate-600">
        Campaigns recorded in the business system. A campaign marked simulated has never been sent to Meta or Google
        and has spent nothing. Live launches require owner approval and a connected ad account (Marketing → Integrations).
      </p>
      <div className="mt-6">
        <LoadState
          resource={campaigns}
          isEmpty={(c) => c.length === 0}
          empty="No campaigns have been created."
        >
          {(list) => (
            <ul className="space-y-2 text-sm">
              {list.map((c) => (
                <li key={c.id} className="rounded-lg border px-3 py-2 text-[#1a1a1a]">
                  <span className="font-medium">{c.name}</span> · {c.platform} · {c.status} · £{c.daily_budget_gbp}/day
                  {c.simulation_only ? <SimulatedBadge /> : null}
                </li>
              ))}
            </ul>
          )}
        </LoadState>
      </div>
    </div>
  );
}
