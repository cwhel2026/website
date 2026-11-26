"use client";

import Link from "next/link";
import { EmptyState, MarketingCard } from "@/components/marketing-director-shell";
import { SimulatedBadge } from "@/components/simulated-badge";
import { describeApiError, useApi } from "@/lib/use-api";

type Campaign = { id: string; name: string; platform: string; status: string; simulation_only: boolean };

function statusLabel(c: Campaign) {
  if (c.status === "live" && !c.simulation_only) {
    return <span className="ml-2 rounded-full bg-emerald-200 px-2 py-0.5 text-xs font-semibold text-emerald-950">LIVE</span>;
  }
  if (c.simulation_only || c.status === "live_simulated") return <SimulatedBadge />;
  return null;
}

export default function CampaignsPage() {
  const campaigns = useApi<Campaign[]>("/api/v1/marketing/campaigns");

  return (
    <>
      <MarketingCard title="Meta lead campaigns">
        <p className="text-xs text-slate-500">
          Consolidated structure — £150/week. Launches require owner approval; simulated campaigns spend nothing.
        </p>
        <Link href="/dashboard/advertising" className="mt-2 inline-block text-sm underline">
          Full campaign manager
        </Link>
      </MarketingCard>
      {campaigns.error ? (
        <div role="alert" className="rounded-lg border border-red-400/40 bg-red-950/40 px-3 py-2 text-sm text-red-100">
          {describeApiError(campaigns.error).title}: {describeApiError(campaigns.error).detail}
        </div>
      ) : campaigns.loading && !campaigns.data ? (
        <p className="text-sm text-white/70">Loading…</p>
      ) : (campaigns.data ?? []).length === 0 ? (
        <EmptyState message="No campaigns in system. Prepare drafts after Meta is connected." />
      ) : (
        <ul className="space-y-2 text-sm text-white">
          {(campaigns.data ?? []).map((c) => (
            <li key={c.id} className="rounded-lg bg-white/10 px-3 py-2">
              {c.name} · {c.status.replace("_", " ")}
              {statusLabel(c)}
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
