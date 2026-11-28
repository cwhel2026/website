"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { PortalError, PortalKpi } from "@/components/portal-ui";

type Director = {signals: Record<string,number>; agents:{slug:string;name:string;mode:string;paused:boolean;emergency_stop:boolean}[]};
type Command = { as_of: string; open_quotes: number; pending_approvals: number; coating_due_within_two_days: number; outstanding_invoice_gbp: string; upcoming_visits: {id:string; reference:string; start:string; type:string; weather_suitable:boolean|null}[]; director_tasks: {id:string; title:string; priority:number}[] };
type Quotation = {
  reference: string;
  total_inc_vat_gbp: number;
  status: string;
  created_at: string;
};
type Enquiry = { id: string; stage: string; created_at: string };
type Analytics = {
  revenue_collected_gbp?: number | string;
  enquiries?: number;
  quotations?: number;
  quotes_accepted?: number;
};
type FinanceStatus = {
  freeagent?: { state?: string; message?: string; can_sync?: boolean };
};
type MarketingOverview = {
  meta_account_spend_7d_gbp?: number | null;
  meta_spend_source?: string;
  growth_fund?: { virtual_reserve_balance_gbp?: number; available_uncommitted_gbp?: number };
};
type Invoice = {
  invoice_number?: string;
  status?: string;
  total_inc_vat_gbp?: number;
  amount_paid_gbp?: number;
};
type Approval = { id: string; title: string; status: string };
type Watchdog = { count?: number; issues?: { title: string; severity: string }[] };

export default function DashboardOverviewPage() {
  const [director,setDirector] = useState<Director|null>(null);
  const [command, setCommand] = useState<Command | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [quotes, setQuotes] = useState<Quotation[]>([]);
  const [enquiries, setEnquiries] = useState<Enquiry[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [finance, setFinance] = useState<FinanceStatus | null>(null);
  const [marketing, setMarketing] = useState<MarketingOverview | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [watchdog, setWatchdog] = useState<Watchdog | null>(null);

  const [target,setTarget]=useState("");
  const [targetResult,setTargetResult]=useState<{recorded_payments_gbp:string;remaining_gbp:string}|null>(null);
  async function reviewTarget(){setTargetResult(null);try{setTargetResult(await apiGet(`/api/v1/business-director/target-review?monthly_target=${encodeURIComponent(target)}`,getToken() ?? undefined));}catch{setScanMessage("Target review unavailable");}}
  const [scanning, setScanning] = useState(false);
  const [scanMessage, setScanMessage] = useState("");
  async function scanDirector() {
    setScanning(true); setScanMessage("");
    try {
      const result = await apiPost<{tasks_created: number}>("/api/v1/business-director/scan", {});
      setScanMessage(`${result.tasks_created} new recommendations`);
      setRefresh(n => n + 1);
    } catch { setScanMessage("Director scan unavailable. Check system health."); }
    finally { setScanning(false); }
  }
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);
  const [updated, setUpdated] = useState<Date | null>(null);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setErrors([]);
    setDirector(null); setCommand(null); setAnalytics(null); setFinance(null); setMarketing(null); setWatchdog(null); setQuotes([]); setEnquiries([]); setInvoices([]); setApprovals([]);
    const authToken = getToken();
    if (!authToken) { setLoading(false); setErrors(['Session unavailable']); return; }
    const token: string = authToken;

    async function load<T>(path: string, apply: (v: T) => void, label: string) {
      try {
        const data = await apiGet<T>(path, token);
        if (active) apply(data);
      } catch {
        if (active) setErrors((e) => [...e, label]);
      }
    }

    void Promise.all([
      load<Director>("/api/v1/business-director/overview",setDirector,"Director signals"),
      load<Command>("/api/v1/analytics/command-centre", setCommand, "Command centre"),
      load<Quotation[]>("/api/v1/quotations", (q) => setQuotes(q), "Quotations"),
      load<Enquiry[]>("/api/v1/crm/enquiries", (e) => setEnquiries(e), "Enquiries"),
      load<Analytics>("/api/v1/analytics/overview", setAnalytics, "Analytics"),
      load<FinanceStatus>("/api/v1/finance/status", setFinance, "Finance status"),
      load<MarketingOverview>("/api/v1/marketing/surfacecoat/overview", setMarketing, "Marketing"),
      load<Invoice[]>("/api/v1/finance/invoices", (i) => setInvoices(i), "Invoices"),
      load<Approval[]>("/api/v1/approvals", (a) => setApprovals(a.filter((x) => x.status === "pending")), "Approvals"),
      load<Watchdog>("/api/v1/finance/insights/watchdog", setWatchdog, "Integration health"),
    ]).then(() => { if (active) { setLoading(false); setUpdated(new Date()); } });
    return () => { active = false; };
  }, [refresh]);

  const revenue = formatGbp(analytics?.revenue_collected_gbp);
  const growthBal = marketing?.growth_fund?.virtual_reserve_balance_gbp;
  const metaConnected = marketing?.meta_account_spend_7d_gbp != null;
  const metaSpend = metaConnected ? formatGbp(marketing!.meta_account_spend_7d_gbp) : marketing ? "Not connected" : "—";
  const metaHint = metaConnected ? undefined : marketing?.meta_spend_source;
  const faState = finance?.freeagent?.state;
  const faLabel =
    faState === "connected" || faState === "ok"
      ? "Connected"
      : faState === "not_configured" || faState === "disconnected"
        ? "Not connected"
        : faState
          ? faState.replaceAll("_", " ")
          : "Unknown";
  const outstandingInvoices = invoices.filter((i) => {
    const total = i.total_inc_vat_gbp ?? 0;
    const paid = i.amount_paid_gbp ?? 0;
    return !['draft','void','paid'].includes(i.status ?? '') && total - paid > 0.01;
  });

  return (
    <div className="max-w-full overflow-x-hidden">
      <header className="relative overflow-hidden rounded-3xl border border-amber-300/20 bg-gradient-to-br from-[#39301c] via-[#20231f] to-[#141716] p-5 sm:p-8">
        <p className="text-xs font-bold uppercase tracking-[.24em] text-amber-300">SurfaceCoat / Operations</p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-5xl">Business command centre</h1>
        <p className="mt-2 text-sm text-white/70">Your operations, money and decisions in one place.</p>
        <div className="mt-6 grid grid-cols-2 gap-3">
          <Link href="/dashboard/approvals" className="rounded-2xl bg-black/30 p-4"><span className="block text-xs text-amber-200">Awaiting approval</span><strong className="mt-1 block text-3xl text-white">{command?.pending_approvals ?? "—"}</strong></Link>
          <Link href="/dashboard/calendar" className="rounded-2xl bg-black/30 p-4"><span className="block text-xs text-amber-200">Coating due · 2 days</span><strong className="mt-1 block text-3xl text-white">{command?.coating_due_within_two_days ?? "—"}</strong></Link>
        </div>
      </header>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        <p role="status" className="text-xs text-white/70">{loading ? "Refreshing business data…" : errors.length ? "Partial data — some services unavailable" : updated ? "Updated " + updated.toLocaleTimeString("en-GB") : "Not loaded"}</p>
        <button disabled={loading} onClick={() => setRefresh(n => n+1)} className="min-h-11 rounded-lg border border-white/20 px-4 text-sm disabled:opacity-50">Refresh</button>
      </div>
      {errors.length > 0 && (
        <PortalError
          message={`Some sections could not load: ${errors.join(", ")}.`}
          detail="Open System health or sign in again if this persists."
        />
      )}

      <Link href="/dashboard/launch-readiness" className="mt-4 flex items-center justify-between rounded-2xl border border-[#eab308]/40 bg-gradient-to-br from-[#3b3218] to-[#242424] p-4"><div><p className="text-xs uppercase tracking-widest text-[#eab308]">Launch centre</p><p className="mt-1 font-semibold">Check operational readiness</p><p className="text-xs text-white/70">Integration evidence and setup steps</p></div><span aria-hidden="true">›</span></Link>
      <h2 className="mt-7 text-lg font-semibold">Business performance</h2>
      <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
        <PortalKpi label="Recorded payments (30d)" value={revenue} />
        <PortalKpi label="FreeAgent" value={faLabel} hint={finance?.freeagent?.message} />
        <PortalKpi label="Growth fund" value={growthBal != null ? formatGbp(growthBal) : "—"} />
        <PortalKpi label="Meta spend (7d)" value={metaSpend} hint={metaHint} />
        <PortalKpi label="New enquiries" value={String(analytics?.enquiries ?? '—')} />
        <PortalKpi
          label="Open quotes"
          value={String(command?.open_quotes ?? "—")}
        />
        <PortalKpi label="Pending approvals" value={String(command?.pending_approvals ?? "—")} />
        <PortalKpi
          label="Finance alerts"
          value={String(watchdog?.count ?? watchdog?.issues?.length ?? "—")}
        />
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2"><PortalKpi label="Coating due within 2 days" value={String(command?.coating_due_within_two_days ?? "—")} /><PortalKpi label="Outstanding invoices" value={formatGbp(command?.outstanding_invoice_gbp)} /></div>
      <h2 className="mt-7 text-lg font-semibold">Your workspace</h2>
      <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
        <QuickLink href="/dashboard/quotations" label="New quote" />
        <QuickLink href="/dashboard/calendar" label="Diary" />
        <QuickLink href="/dashboard/marketing/overview" label="Marketing" />
        <QuickLink href="/dashboard/finance-hub" label="Money hub" />
        <QuickLink href="/dashboard/approvals" label="Approvals" />
        <QuickLink href="/dashboard/assistant" label="AI assistant" />
        <QuickLink href="/dashboard/weather" label="Weather intelligence" />
        <QuickLink href="/dashboard/customers" label="Customer CRM" />
        <QuickLink href="/dashboard/system-health" label="Telegram & system" />
      </div>

      <section className="mt-7 rounded-3xl border border-amber-300/25 bg-gradient-to-br from-[#302a1b] to-[#202320] p-5">
        <h2 className="font-semibold text-[#eab308]">Business director</h2>
        <p className="mt-1 text-sm text-white/70">Review approvals, coating priorities, stock and overdue invoices.</p>
        <button onClick={() => void scanDirector()} disabled={scanning || loading} className="mt-3 min-h-11 rounded-lg bg-[#eab308] px-4 font-semibold text-black disabled:opacity-50">{scanning ? "Scanning…" : "Scan business"}</button>
        <p role="status" className="mt-2 text-sm">{scanMessage}</p>
        <div className="mt-4 grid grid-cols-2 gap-2">{director ? Object.entries(director.signals).map(([key,count])=><PortalKpi key={key} label={key.replaceAll("_"," ")} value={String(count)}/>) : <p>Director signals unavailable.</p>}</div>
        <div className="mt-4 space-y-2">{director?.agents.map(a=><div key={a.slug} className="flex justify-between gap-2 rounded border border-white/10 p-2 text-sm"><span>{a.name}</span><span>{a.emergency_stop?"Stopped":a.paused?"Paused":a.mode}</span></div>)}</div>
        <div className="mt-4 rounded border border-white/10 p-3"><label className="block text-sm">Monthly payment target (£)<input type="number" min="1" value={target} onChange={e=>{setTarget(e.target.value);setTargetResult(null)}} className="mt-1 block w-full rounded bg-black/30 p-2"/></label><button disabled={!Number.isFinite(Number(target))||Number(target)<=0} onClick={()=>void reviewTarget()} className="mt-2 rounded border px-3 py-2">Review target</button>{targetResult&&<p className="mt-2 text-sm">Recorded payments: {formatGbp(targetResult.recorded_payments_gbp)} · Remaining: {formatGbp(targetResult.remaining_gbp)}</p>}<p className="text-xs text-white/60">Recorded payments, not verified bank cash.</p></div>
        <p className="mt-3 text-xs text-white/70">Recommendations only. External actions require separate approval.</p>
      </section>
      <div className="mt-8 grid gap-4 md:grid-cols-2">
        <ListSection title="Recent quotations" empty={loading ? "Loading…" : errors.includes("Quotations") ? "Unavailable" : "No quotations yet."} items={quotes.length}>
          {quotes.slice(0,5).map((q) => (
            <li key={q.reference} className="rounded-lg border border-white/10 bg-[#1a1a1a]/40 px-3 py-2">
              {q.reference} · {formatGbp(q.total_inc_vat_gbp)} · {q.status}
            </li>
          ))}
        </ListSection>
        <ListSection title="Recent enquiries" empty={loading ? "Loading…" : errors.includes("Enquiries") ? "Unavailable" : "No enquiries yet."} items={enquiries.length}>
          {enquiries.slice(0,5).map((e) => (
            <li key={e.id} className="rounded-lg border border-white/10 bg-[#1a1a1a]/40 px-3 py-2">
              {e.stage} · {new Date(e.created_at).toLocaleString("en-GB")}
            </li>
          ))}
        </ListSection>
        <ListSection title="Upcoming jobs" empty={command ? "No scheduled jobs." : "Schedule unavailable."} items={command?.upcoming_visits.length ?? 0}>
          {command?.upcoming_visits.map(v => <li key={v.id} className="rounded-lg border border-white/10 p-3"><p className="font-semibold">{v.reference} · {v.type}</p><p>{new Date(v.start).toLocaleString("en-GB",{timeZone:"Europe/London"})}</p><p className="text-xs text-white/70">Recorded weather: {v.weather_suitable == null ? "Not assessed" : v.weather_suitable ? "Suitable" : "Unsuitable"}</p></li>)}
        </ListSection>
        <ListSection title="Outstanding invoices" empty={loading ? "Loading…" : errors.includes("Invoices") ? "Unavailable" : "No outstanding invoices."} items={outstandingInvoices.length}>
          {outstandingInvoices.slice(0,5).map((inv, i) => (
            <li key={inv.invoice_number ?? i} className="rounded-lg border border-white/10 bg-[#1a1a1a]/40 px-3 py-2">
              {inv.invoice_number ?? "Invoice"} · {inv.status} ·{" "}
              {formatGbp((inv.total_inc_vat_gbp ?? 0) - (inv.amount_paid_gbp ?? 0))}
            </li>
          ))}
        </ListSection>
        <ListSection title="AI recommendations" empty={command ? "No open director tasks." : "Director data unavailable."} items={command?.director_tasks.length ?? 0}>
          {command?.director_tasks.map((t) => (
            <li key={t.id} className="rounded-lg border border-white/10 bg-[#1a1a1a]/40 px-3 py-2">
              {t.title}
              {t.priority ? ` · ${t.priority}` : ""}
            </li>
          ))}
        </ListSection>
        <ListSection title="Pending approvals" empty={loading ? "Loading…" : errors.includes("Approvals") ? "Unavailable" : "Nothing waiting for approval."} items={approvals.length}>
          {approvals.slice(0,5).map((a) => (
            <li key={a.id} className="rounded-lg border border-white/10 bg-[#1a1a1a]/40 px-3 py-2">
              {a.title}
            </li>
          ))}
        </ListSection>
      </div>
    </div>
  );
}

function formatGbp(v: number | string | null | undefined): string {
  if (v == null || v === "") return "—";
  const n = typeof v === "string" ? Number(v) : v;
  if (Number.isNaN(n)) return String(v);
  return `£${n.toFixed(2)}`;
}

function QuickLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="flex min-h-20 items-center justify-between gap-2 rounded-2xl border border-white/10 bg-[#222624] p-4 text-sm font-semibold text-white hover:border-amber-300/50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-amber-300"
    >
      {label}<span aria-hidden="true" className="text-amber-300">↗</span>
    </Link>
  );
}

function ListSection({
  title,
  empty,
  items,
  children,
}: {
  title: string;
  empty: string;
  items: number;
  children: React.ReactNode;
}) {
  return (
    <section className="min-w-0 rounded-3xl border border-white/10 bg-[#202422] p-4 sm:p-5">
      <h2 className="text-sm font-semibold text-[#eab308]">{title}</h2>
      {items === 0 ? (
        <p className="mt-2 text-sm text-white/50">{empty}</p>
      ) : (
        <ul className="mt-2 space-y-2 text-sm text-white/90">{children}</ul>
      )}
    </section>
  );
}
