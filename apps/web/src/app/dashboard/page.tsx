"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { PortalError, PortalKpi, PortalPageTitle } from "@/components/portal-ui";

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
type Job = {
  id: string;
  reference?: string;
  status?: string;
  appointments?: { scheduled_start?: string | null; status?: string }[];
};
type Approval = { id: string; title: string; status: string };
type DirectorTask = { id: string; title: string; priority?: string };
type Watchdog = { count?: number; issues?: { title: string; severity: string }[] };

export default function DashboardOverviewPage() {
  const [errors, setErrors] = useState<string[]>([]);
  const [quotes, setQuotes] = useState<Quotation[]>([]);
  const [enquiries, setEnquiries] = useState<Enquiry[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [finance, setFinance] = useState<FinanceStatus | null>(null);
  const [marketing, setMarketing] = useState<MarketingOverview | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [tasks, setTasks] = useState<DirectorTask[]>([]);
  const [watchdog, setWatchdog] = useState<Watchdog | null>(null);

  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);
  const [updated, setUpdated] = useState<Date | null>(null);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setErrors([]);
    const authToken = getToken();
    if (!authToken) return;
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
      load<Quotation[]>("/api/v1/quotations", (q) => setQuotes(q), "Quotations"),
      load<Enquiry[]>("/api/v1/crm/enquiries", (e) => setEnquiries(e), "Enquiries"),
      load<Analytics>("/api/v1/analytics/overview", setAnalytics, "Analytics"),
      load<FinanceStatus>("/api/v1/finance/status", setFinance, "Finance status"),
      load<MarketingOverview>("/api/v1/marketing/surfacecoat/overview", setMarketing, "Marketing"),
      load<Invoice[]>("/api/v1/finance/invoices", (i) => setInvoices(i), "Invoices"),
      load<Job[]>("/api/v1/jobs", (j) =>
        setJobs(
          j
            .filter((x) => !['completed', 'cancelled'].includes(x.status ?? '') && nextAppointment(x) !== undefined)
            .sort((a,b) => Date.parse(nextAppointment(a)!) - Date.parse(nextAppointment(b)!)),
        ),
      "Jobs"),
      load<Approval[]>("/api/v1/approvals", (a) => setApprovals(a.filter((x) => x.status === "pending")), "Approvals"),
      load<DirectorTask[]>("/api/v1/business-director/tasks", (t) => setTasks(t.slice(0, 5)), "AI tasks"),
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
  const openQuotes = quotes.filter((q) => !["accepted", "declined", "rejected", "expired"].includes(q.status.toLowerCase()));
  const outstandingInvoices = invoices.filter((i) => {
    const total = i.total_inc_vat_gbp ?? 0;
    const paid = i.amount_paid_gbp ?? 0;
    return !['draft','void','paid'].includes(i.status ?? '') && total - paid > 0.01;
  });

  return (
    <div className="max-w-full overflow-x-hidden">
      <PortalPageTitle
        title="Business overview"
        subtitle="Live data from your connected services — empty when nothing is recorded yet."
      />

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

      <div className="mt-4 grid grid-cols-2 gap-2 md:grid-cols-3 lg:grid-cols-4">
        <PortalKpi label="Revenue (30d)" value={revenue} />
        <PortalKpi label="FreeAgent" value={faLabel} hint={finance?.freeagent?.message} />
        <PortalKpi label="Growth fund" value={growthBal != null ? formatGbp(growthBal) : "—"} />
        <PortalKpi label="Meta spend (7d)" value={metaSpend} hint={metaHint} />
        <PortalKpi label="New enquiries" value={String(analytics?.enquiries ?? '—')} />
        <PortalKpi
          label="Open quotes"
          value={loading || errors.includes("Quotations") ? "—" : String(openQuotes.length)}
        />
        <PortalKpi label="Pending approvals" value={loading || errors.includes("Approvals") ? "—" : String(approvals.length)} />
        <PortalKpi
          label="Finance alerts"
          value={String(watchdog?.count ?? watchdog?.issues?.length ?? "—")}
        />
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        <QuickLink href="/dashboard/quotations" label="New quote" />
        <QuickLink href="/dashboard/calendar" label="Diary" />
        <QuickLink href="/dashboard/marketing/overview" label="Marketing" />
        <QuickLink href="/dashboard/finance-hub" label="Money hub" />
        <QuickLink href="/dashboard/approvals" label="Approvals" />
        <QuickLink href="/dashboard/assistant" label="AI assistant" />
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-2">
        <ListSection title="Recent quotations" empty="No quotations yet." items={quotes.length}>
          {quotes.slice(0,5).map((q) => (
            <li key={q.reference} className="rounded-lg border border-white/10 bg-[#1a1a1a]/40 px-3 py-2">
              {q.reference} · {formatGbp(q.total_inc_vat_gbp)} · {q.status}
            </li>
          ))}
        </ListSection>
        <ListSection title="Recent enquiries" empty="No enquiries yet." items={enquiries.length}>
          {enquiries.slice(0,5).map((e) => (
            <li key={e.id} className="rounded-lg border border-white/10 bg-[#1a1a1a]/40 px-3 py-2">
              {e.stage} · {new Date(e.created_at).toLocaleString("en-GB")}
            </li>
          ))}
        </ListSection>
        <ListSection title="Upcoming jobs" empty="No scheduled jobs." items={jobs.length}>
          {jobs.slice(0,5).map((j) => (
            <li key={j.id} className="rounded-lg border border-white/10 bg-[#1a1a1a]/40 px-3 py-2">
              {j.reference ?? j.id.slice(0, 8)} · {j.status}
              {nextAppointment(j)
                ? ` · ${new Date(nextAppointment(j)!).toLocaleDateString("en-GB")}`
                : ""}
            </li>
          ))}
        </ListSection>
        <ListSection title="Outstanding invoices" empty="No outstanding invoices." items={outstandingInvoices.length}>
          {outstandingInvoices.slice(0,5).map((inv, i) => (
            <li key={inv.invoice_number ?? i} className="rounded-lg border border-white/10 bg-[#1a1a1a]/40 px-3 py-2">
              {inv.invoice_number ?? "Invoice"} · {inv.status} ·{" "}
              {formatGbp((inv.total_inc_vat_gbp ?? 0) - (inv.amount_paid_gbp ?? 0))}
            </li>
          ))}
        </ListSection>
        <ListSection title="AI recommendations" empty="No open director tasks." items={tasks.length}>
          {tasks.map((t) => (
            <li key={t.id} className="rounded-lg border border-white/10 bg-[#1a1a1a]/40 px-3 py-2">
              {t.title}
              {t.priority ? ` · ${t.priority}` : ""}
            </li>
          ))}
        </ListSection>
        <ListSection title="Pending approvals" empty="Nothing waiting for approval." items={approvals.length}>
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
      className="rounded-full border border-[#eab308]/40 bg-[#eab308]/15 inline-flex min-h-11 items-center px-4 py-2 text-xs font-semibold text-[#eab308]"
    >
      {label}
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
    <section>
      <h2 className="text-sm font-semibold text-[#eab308]">{title}</h2>
      {items === 0 ? (
        <p className="mt-2 text-sm text-white/50">{empty}</p>
      ) : (
        <ul className="mt-2 space-y-2 text-sm text-white/90">{children}</ul>
      )}
    </section>
  );
}
function nextAppointment(job: Job): string | undefined {
  return job.appointments?.filter(a => a.status === "confirmed" && a.scheduled_start && Date.parse(a.scheduled_start) > Date.now()).map(a => a.scheduled_start!).sort((a,b) => Date.parse(a)-Date.parse(b))[0];
}
