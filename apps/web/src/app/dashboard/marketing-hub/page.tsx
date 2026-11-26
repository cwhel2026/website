"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type DailyPlan = {
  priority_actions?: Array<{ action: string; reason?: string; certainty?: string }>;
  budget_policy?: { live_paid_spend_approved: boolean; emergency_pause_all: boolean };
  weekly_spend?: { total_spent_gbp: number; by_platform: Record<string, number> };
};

type Budget = {
  policy: {
    live_paid_spend_approved: boolean;
    emergency_pause_all: boolean;
    daily_limit_gbp: number;
    meta_daily_limit_gbp: number;
    google_daily_limit_gbp: number;
  };
};

type BrandProfile = { business_name: string; tone_of_voice?: string; service_areas?: string[] };
type CompetitorRow = { competitor_name: string; confidence: number; source_name: string };
type Profitability = { marketing_roi: number | null; job_contribution_gbp: number | null; optimise_for?: string };

export default function MarketingHubPage() {
  const [plan, setPlan] = useState<DailyPlan | null>(null);
  const [budget, setBudget] = useState<Budget | null>(null);
  const [prospects, setProspects] = useState<
    Array<{ business_name: string; lead_score: number; pipeline_stage?: string }>
  >([]);
  const [brand, setBrand] = useState<BrandProfile | null>(null);
  const [competitors, setCompetitors] = useState<CompetitorRow[]>([]);
  const [profit, setProfit] = useState<Profitability | null>(null);
  const [compArea, setCompArea] = useState("Preston");
  const [searchQuery, setSearchQuery] = useState("car park Preston");
  const [searchMsg, setSearchMsg] = useState<string | null>(null);

  const token = getToken();

  const reload = () => {
    if (!token) return;
    apiGet<DailyPlan>("/api/v1/marketing/director/daily-plan", token).then(setPlan).catch(() => setPlan(null));
    apiGet<Budget>("/api/v1/marketing/budget", token).then(setBudget).catch(() => setBudget(null));
    apiGet<Array<{ business_name: string; lead_score: number; pipeline_stage?: string }>>(
      "/api/v1/marketing/commercial-prospects",
      token,
    )
      .then(setProspects)
      .catch(() => setProspects([]));
    apiGet<BrandProfile>("/api/v1/marketing/launch/brand", token).then(setBrand).catch(() => setBrand(null));
    apiGet<{ findings: CompetitorRow[] }>("/api/v1/marketing/launch/competitors", token)
      .then((r) => setCompetitors(r.findings || []))
      .catch(() => setCompetitors([]));
    apiGet<Profitability>("/api/v1/marketing/launch/profitability?days=90", token)
      .then(setProfit)
      .catch(() => setProfit(null));
  };

  useEffect(() => {
    reload();
  }, [token]);

  const toggleLiveSpend = async () => {
    if (!token || !budget) return;
    await apiPatch(
      "/api/v1/marketing/budget",
      { live_paid_spend_approved: !budget.policy.live_paid_spend_approved },
      token,
    );
    reload();
  };

  const runCompetitorResearch = async () => {
    if (!token) return;
    await apiPost("/api/v1/marketing/launch/competitors/research", { area: compArea }, token);
    reload();
  };

  const runSearch = async () => {
    if (!token) return;
    setSearchMsg(null);
    const res = await apiPost<{ ok?: boolean; imported?: number; message?: string }>(
      "/api/v1/marketing/commercial-prospects/search",
      { query: searchQuery, limit: 20 },
      token,
    );
    setSearchMsg(res.message || (res.ok ? `Imported ${res.imported} prospects` : "Search finished"));
    reload();
  };

  return (
    <div className="max-w-2xl space-y-8 pb-16">
      <header>
        <h1 className="text-2xl font-semibold text-emerald-950">Marketing command centre</h1>
        <p className="mt-2 text-sm text-slate-600">
          Diary-led growth — live ad spend stays off until you approve it below.
        </p>
      </header>

      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="font-semibold text-slate-900">Budget controls</h2>
        {budget && (
          <div className="mt-3 space-y-2 text-sm">
            <p>
              Live paid spend:{" "}
              <span className={budget.policy.live_paid_spend_approved ? "text-emerald-700" : "text-amber-700"}>
                {budget.policy.live_paid_spend_approved ? "Approved" : "Blocked (default)"}
              </span>
            </p>
            <button
              type="button"
              onClick={toggleLiveSpend}
              className="rounded-lg bg-emerald-700 px-4 py-2 text-white"
            >
              {budget.policy.live_paid_spend_approved ? "Revoke live spend approval" : "Approve live spend"}
            </button>
            {plan?.weekly_spend && (
              <p className="text-slate-600">Recorded spend (7d): £{plan.weekly_spend.total_spent_gbp.toFixed(2)}</p>
            )}
          </div>
        )}
      </section>

      <section className="rounded-xl border p-4">
        <h2 className="font-semibold">AI director — today</h2>
        <ul className="mt-3 space-y-2 text-sm">
          {(plan?.priority_actions || []).map((a, i) => (
            <li key={i} className="rounded border border-emerald-100 bg-emerald-50/50 px-3 py-2">
              <p className="font-medium">{a.action}</p>
              {a.reason && <p className="text-slate-600">{a.reason}</p>}
              {a.certainty && <p className="text-xs text-slate-500">({a.certainty})</p>}
            </li>
          ))}
          {!plan?.priority_actions?.length && <li className="text-slate-500">Loading plan…</li>}
        </ul>
      </section>

      <section className="rounded-xl border p-4">
        <h2 className="font-semibold">Brand intelligence</h2>
        {brand && (
          <p className="mt-2 text-sm text-slate-600">
            {brand.business_name} · {(brand.service_areas || []).slice(0, 4).join(", ")}
          </p>
        )}
        <Link href="/dashboard/marketing-integrations" className="mt-2 inline-block text-sm text-emerald-800 underline">
          Integrations & launch readiness
        </Link>
      </section>

      <section className="rounded-xl border p-4">
        <h2 className="font-semibold">Competitor intelligence</h2>
        <div className="mt-2 flex gap-2">
          <input
            className="flex-1 rounded border px-2 py-1 text-sm"
            value={compArea}
            onChange={(e) => setCompArea(e.target.value)}
          />
          <button type="button" onClick={runCompetitorResearch} className="rounded bg-slate-800 px-3 py-1 text-sm text-white">
            Research
          </button>
        </div>
        <ul className="mt-2 max-h-32 overflow-y-auto text-xs text-slate-600">
          {competitors.slice(0, 8).map((c, i) => (
            <li key={i}>
              {c.competitor_name} · {c.source_name} · confidence {c.confidence}
            </li>
          ))}
          {!competitors.length && <li>Run research when Places API is configured (mock-safe without key).</li>}
        </ul>
      </section>

      {profit && (
        <section className="rounded-xl border p-4 text-sm">
          <h2 className="font-semibold">Profitability (90d)</h2>
          <p className="mt-2">
            ROI: {profit.marketing_roi ?? "unknown"} · Job contribution: {profit.job_contribution_gbp ?? "unknown"}
          </p>
          <p className="text-xs text-slate-500">Optimise for: {profit.optimise_for || "profitable work"}</p>
        </section>
      )}

      <section className="rounded-xl border p-4">
        <h2 className="font-semibold">Commercial prospects</h2>
        <div className="mt-2 flex gap-2">
          <input
            className="flex-1 rounded border px-2 py-1 text-sm"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button type="button" onClick={runSearch} className="rounded bg-slate-800 px-3 py-1 text-sm text-white">
            Search CH
          </button>
        </div>
        {searchMsg && <p className="mt-2 text-xs text-slate-600">{searchMsg}</p>}
        <ul className="mt-3 max-h-48 overflow-y-auto text-sm">
          {prospects.slice(0, 15).map((p, i) => (
            <li key={i}>
              {p.business_name} · score {p.lead_score}
              {p.pipeline_stage ? ` · ${p.pipeline_stage}` : ""}
            </li>
          ))}
        </ul>
      </section>

      <nav className="grid grid-cols-2 gap-2 text-sm">
        <Link href="/dashboard/advertising" className="rounded border px-3 py-2 text-center">
          Campaigns
        </Link>
        <Link href="/dashboard/commercial-leads" className="rounded border px-3 py-2 text-center">
          Legacy leads
        </Link>
        <Link href="/dashboard/marketing" className="rounded border px-3 py-2 text-center">
          Territory capacity
        </Link>
        <Link href="/dashboard/flyers" className="rounded border px-3 py-2 text-center">
          Flyers
        </Link>
      </nav>
    </div>
  );
}