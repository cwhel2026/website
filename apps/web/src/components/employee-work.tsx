"use client";
import { useEffect } from "react";
import Link from "next/link";
import { useApi } from "@/lib/use-api";

type Work = {id: string; title: string; agent: string; status: string; attempts: number; result: null | {summary?: string; error?: string; campaign_id?: string; plan?: {launch_blockers?: string[]; research_status?: string; budget?: {total_gbp: string; safety_buffer_pct: string}; scenarios?: Record<string, {forecast: {reach: string; enquiries: string; jobs: string; fulfillable_jobs: string}}>}}};
export function EmployeeWork() {
  const {data, loading, error, reload} = useApi<Work[]>("/api/v1/business-director/employee-work");
  useEffect(() => {const timer = setInterval(() => {if (!document.hidden) reload();}, 15000); return () => clearInterval(timer);}, [reload]);
  return <section className="rounded-2xl border border-white/10 bg-[#202422] p-4 text-white">
    <div className="flex items-center justify-between gap-3"><h2 className="font-semibold">Employee work</h2><button onClick={reload} className="rounded border border-white/30 px-3 py-2 text-sm">Refresh</button></div>
    {error ? <p role="alert">Could not load employee work. Refresh to retry.</p> : loading && !data ? <p>Loading…</p> : !data?.length ? <p className="mt-2 text-sm text-white/60">No saved work yet. Ask your employees in Telegram to prepare a campaign or review finances and operations.</p> : data.map(item => <details key={item.id} className="mt-3 rounded-lg bg-white/5 p-3">
      <summary className="cursor-pointer">{item.title} <span className="text-amber-300">· {item.status.replaceAll("_", " ")}</span></summary>
      <p className="mt-3 text-sm">{item.result?.summary ?? item.result?.error ?? `Waiting for execution. Attempts: ${item.attempts}.`}</p>
      {item.result?.plan?.budget && <p className="mt-2 text-sm">Proposed seven-day budget: £{item.result.plan.budget.total_gbp}. Safety buffer: {item.result.plan.budget.safety_buffer_pct}%. No spend authorised.</p>}
      {item.result?.plan?.scenarios && <div className="mt-3 overflow-x-auto"><p className="text-xs text-white/60">Illustrative assumptions, not Meta estimates or guaranteed outcomes.</p><table className="mt-2 w-full text-left text-xs"><thead><tr><th>Scenario</th><th>Reach</th><th>Enquiries</th><th>Demand</th><th>Capacity-limited jobs</th></tr></thead><tbody>{Object.entries(item.result.plan.scenarios).map(([name, s]) => <tr key={name}><td className="py-2 pr-2">{name.replaceAll("_", " ")}</td><td>{s.forecast.reach}</td><td>{s.forecast.enquiries}</td><td>{s.forecast.jobs}</td><td>{s.forecast.fulfillable_jobs}</td></tr>)}</tbody></table></div>}
      {item.result?.plan?.launch_blockers && <><h3 className="mt-3 text-sm font-semibold">Before launch</h3><ul className="list-disc pl-5 text-sm">{item.result.plan.launch_blockers.map(b => <li key={b}>{b}</li>)}</ul></>}
      {item.result?.campaign_id && <Link className="mt-3 inline-block text-sm underline" href="/dashboard/advertising">Review saved campaign</Link>}
      <p className="mt-2 break-all text-xs text-white/50">Reference: {item.id}</p>
    </details>)}
  </section>;
}
