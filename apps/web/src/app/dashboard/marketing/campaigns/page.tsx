"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { EmptyState, MarketingCard } from "@/components/marketing-director-shell";

type Campaign = { id: string; name: string; platform: string; status: string; simulation_only: boolean };

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Campaign[]>("/api/v1/marketing/campaigns", token).then(setCampaigns).catch(() => setCampaigns([]));
  }, []);

  return (
    <>
      <MarketingCard title="Meta lead campaigns">
        <p className="text-xs text-slate-500">
          Consolidated structure — £150/week. Launches require approval; no fictional spend.
        </p>
        <Link href="/dashboard/advertising" className="mt-2 inline-block text-sm underline">
          Full campaign manager
        </Link>
      </MarketingCard>
      {campaigns.length === 0 ? (
        <EmptyState message="No campaigns in system. Prepare drafts after Meta is connected." />
      ) : (
        <ul className="space-y-2 text-sm text-white">
          {campaigns.map((c) => (
            <li key={c.id} className="rounded-lg bg-white/10 px-3 py-2">
              {c.name} · {c.status}
              {c.simulation_only ? " · draft/simulation" : " · live"}
            </li>
          ))}
        </ul>
      )}
    </>
  );
}