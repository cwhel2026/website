"use client";
import Link from "next/link";
import { useState } from "react";
import { apiPost } from "@/lib/api";
import { useApi } from "@/lib/use-api";

type Readiness = { items: {key:string;label:string;status:string}[]; external_blockers:string[] };
type Evidence = { label:string; state:string; detail:string; href:string };
export default function LaunchCentre() {
  const marketing = useApi<Readiness>("/api/v1/marketing/launch/readiness");
  const schema = useApi<{ok:boolean; alembic_current:string}>("/api/v1/ops/schema");
  const workers = useApi<{overall:string;broker_reachable:boolean|null;never_run:string[]}>("/api/v1/ops/workers");
  const finance = useApi<{freeagent?:{state:string;message:string}}>("/api/v1/finance/status");
  const telegram = useApi<{status:string;delivered_at:string|null;title:string}[]>("/api/v1/notifications/outbox");
  const [message,setMessage] = useState("");
  const [busy,setBusy] = useState(false);
  const evidence: Evidence[] = [
    {label:"Database schema",state:schema.data?.ok ? "Verified" : schema.data ? "Blocked" : "Unverified",detail:schema.data?.alembic_current ?? "Check database migration status",href:"/dashboard/system-health"},
    {label:"Background automation",state:workers.data?.overall === "ok" && workers.data.never_run.length === 0 ? "Verified" : workers.data ? "Review required" : "Unverified",detail:workers.data?.overall ?? "Configure Redis and worker service",href:"/dashboard/system-health"},
    {label:"FreeAgent",state:finance.data?.freeagent?.state ?? "Unverified",detail:"Connect OAuth and verify a complete import; connection alone is not readiness.",href:"/dashboard/finance-hub"},
    {label:"Telegram",state:telegram.data?.some(r=>r.status==="delivered" && r.delivered_at) ? "Historical delivery recorded" : "Unverified",detail:"Send an owner test and verify incoming webhook separately.",href:"/dashboard/system-health"},
    {label:"Persistent media & backups",state:"Manual verification required",detail:"Mount Railway storage and perform a backup restore test.",href:"/dashboard/system-health"},
    {label:"Weather",state:"Manual verification required",detail:"Check live forecasts for booked properties before confirming coating.",href:"/dashboard/weather"},
  ];
  async function pause() {
    if (!window.confirm("Pause all advertising in SurfaceCoat? Verify external platform delivery separately.")) return;
    setBusy(true);setMessage("");
    try { await apiPost("/api/v1/marketing/launch/pause-all-advertising",{});setMessage("Local pause requested successfully. Verify external campaigns separately.");marketing.reload(); }
    catch {setMessage("Pause request failed. Check advertising platforms directly.");}
    finally {setBusy(false);}
  }
  return <div className="space-y-5">
    <header><p className="text-xs font-semibold uppercase tracking-widest text-[#eab308]">SurfaceCoat · operations</p><h1 className="text-3xl font-semibold">Launch centre</h1><p className="mt-2 text-sm text-white/70">Evidence and setup steps. Configuration is not proof of a working integration.</p></header>
    <button className="min-h-11 rounded-lg border border-white/20 px-4" onClick={()=>{marketing.reload();schema.reload();workers.reload();finance.reload();telegram.reload();}}>Refresh evidence</button>
    <section className="grid gap-3 sm:grid-cols-2">{evidence.map(e=><article key={e.label} className="rounded-2xl border border-white/10 bg-[#242424] p-4"><h2 className="font-semibold">{e.label}</h2><p className="mt-2 text-sm font-medium text-[#eab308]">{e.state}</p><p className="mt-2 text-sm text-white/70">{e.detail}</p><Link href={e.href} className="mt-3 inline-flex min-h-11 items-center text-sm underline">Open setup</Link></article>)}</section>
    <section className="rounded-2xl border border-white/10 p-4"><h2 className="font-semibold">External launch checklist</h2>{!marketing.data ? <p className="mt-2 text-sm">Checklist unavailable or loading.</p> : <ul className="mt-2 divide-y divide-white/10">{marketing.data.items.map(i=><li key={i.key} className="flex flex-wrap justify-between gap-2 py-3 text-sm"><span>{i.label}</span><span className="text-white/70">{i.status.replaceAll("_"," ")}</span></li>)}</ul>}<Link href="/dashboard/marketing/integrations" className="inline-flex min-h-11 items-center underline">Integration setup</Link></section>
    <section className="rounded-2xl border border-red-500/40 p-4"><h2 className="font-semibold">Spending safety</h2><p className="mt-2 text-sm text-white/70">Keep live spending blocked until owner approval and external verification.</p><button disabled={busy} onClick={()=>void pause()} className="mt-3 min-h-11 w-full rounded-lg bg-red-800 px-4 text-white disabled:opacity-50">Emergency pause advertising</button><p role="status" className="mt-2 text-sm">{message}</p></section>
  </div>;
}
