"use client";

import { useEffect, useState } from "react";
import { apiGet, ApiError } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { EmptyState, MarketingCard } from "@/components/marketing-director-shell";
import { gbp } from "@/lib/format";

type Overview = {
  pre_launch_mode?: boolean;
  weekly_budget_gbp?: number;
  remaining_budget_estimate_gbp?: number;
  meta_account_spend_7d_gbp?: number | null;
  meta_spend_source?: string;
  organic_posts_total?: number;
  director_mode?: string;
  emergency_pause?: boolean;
  growth_fund?: { virtual_reserve_balance_gbp?: number; available_uncommitted_gbp?: number };
  disclaimer?: string;
  degraded?: string[];
};

export default function MarketingOverviewPage() {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorDetail, setErrorDetail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Overview>("/api/v1/marketing/surfacecoat/overview", token)
      .then(setData)
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          setError(`Marketing overview failed (${err.status}).`);
          setErrorDetail(err.message);
        } else {
          setError("Unable to load marketing overview. Check API connection.");
        }
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <EmptyState message="Loading…" />;
  if (error) {
    return (
      <div className="space-y-2">
        <EmptyState message={error} />
        {errorDetail ? <p className="text-xs text-white/55">{errorDetail}</p> : null}
      </div>
    );
  }

  return (
    <>
      {data?.pre_launch_mode && (
        <p className="mb-4 rounded-lg border border-[#eab308]/40 bg-[#eab308]/10 px-3 py-2 text-sm text-[#eab308]">
          Pre-launch: no live ad spend until you approve it in Budget.
        </p>
      )}
      {data?.degraded?.length ? (
        <p className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-100">
          Partial data: {data.degraded.join(", ").replaceAll("_", " ")}
        </p>
      ) : null}
      <MarketingCard title="This week">
        <dl className="grid grid-cols-2 gap-3">
          <Stat label="Weekly cap" value={`£${data?.weekly_budget_gbp ?? "—"}`} />
          <Stat label="Remaining (est.)" value={gbp(data?.remaining_budget_estimate_gbp, "—")} />
          <Stat label="Meta spend (7d)" value={formatSpend(data)} />
          <Stat label="Organic posts" value={String(data?.organic_posts_total ?? 0)} />
        </dl>
        {data?.meta_spend_source && data.meta_spend_source !== "meta_api" && (
          <p className="mt-2 text-xs text-slate-500">Meta: {data.meta_spend_source}</p>
        )}
      </MarketingCard>
      {data?.growth_fund ? (
        <MarketingCard title="Growth fund">
          <p className="text-sm">
            Virtual reserve {gbp(data.growth_fund.virtual_reserve_balance_gbp, "Unavailable")} · Available{" "}
            {gbp(data.growth_fund.available_uncommitted_gbp, "Unavailable")}
          </p>
        </MarketingCard>
      ) : (
        <MarketingCard title="Growth fund">
          <p className="text-sm text-slate-600">Growth fund data unavailable — check finance migrations.</p>
        </MarketingCard>
      )}
      <MarketingCard title="Director mode">
        <p className="capitalize">{data?.director_mode?.replace("_", " ") ?? "recommend"}</p>
        {data?.emergency_pause && <p className="mt-2 text-red-700">Emergency pause is ON</p>}
      </MarketingCard>
      <p className="text-xs text-white/60">{data?.disclaimer}</p>
    </>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className="text-lg font-semibold">{value}</dd>
    </div>
  );
}

function formatSpend(data: Overview | null) {
  if (data?.meta_account_spend_7d_gbp == null) return "Not connected";
  return gbp(data.meta_account_spend_7d_gbp);
}