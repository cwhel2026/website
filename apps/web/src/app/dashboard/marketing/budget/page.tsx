"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { MarketingCard } from "@/components/marketing-director-shell";

type Budget = { policy: Record<string, unknown> };

export default function BudgetPage() {
  const [budget, setBudget] = useState<Budget | null>(null);
  const token = getToken();

  const load = () => {
    if (!token) return;
    apiGet<Budget>("/api/v1/marketing/budget", token).then(setBudget).catch(() => setBudget(null));
  };

  useEffect(load, [token]);

  async function emergencyPause() {
    if (!token) return;
    await apiPost("/api/v1/marketing/emergency-pause", {}, token);
    load();
  }

  async function toggleLive() {
    if (!token || !budget?.policy) return;
    await apiPatch(
      "/api/v1/marketing/budget",
      { live_paid_spend_approved: !budget.policy.live_paid_spend_approved },
      token,
    );
    load();
  }

  const p = budget?.policy || {};
  return (
    <>
      <MarketingCard title="Budget protection">
        <dl className="space-y-2 text-sm">
          <Row label="Weekly cap" value={`£${p.weekly_limit_gbp ?? 150}`} />
          <Row label="Meta daily cap" value={`£${p.meta_daily_limit_gbp ?? 22}`} />
          <Row label="Live spend approved" value={p.live_paid_spend_approved ? "Yes" : "No"} />
          <Row label="Emergency pause" value={p.emergency_pause_all ? "ACTIVE" : "Off"} />
        </dl>
        <button
          type="button"
          onClick={toggleLive}
          className="mt-4 w-full rounded-full border border-[#1a1a1a] py-2 text-sm"
        >
          {p.live_paid_spend_approved ? "Revoke live spend approval" : "Approve live spend (owner)"}
        </button>
        <button
          type="button"
          onClick={emergencyPause}
          className="mt-2 w-full rounded-full bg-red-700 py-2 text-sm text-white"
        >
          Emergency pause all ads
        </button>
        <p className="mt-3 text-xs text-slate-500">
          Internal caps do not guarantee Meta-side limits. Use account spending limits in Ads Manager where available.
        </p>
      </MarketingCard>
    </>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}