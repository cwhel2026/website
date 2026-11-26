"use client";

import { useState } from "react";
import { LoadState } from "@/components/load-state";
import { apiPost } from "@/lib/api";
import { describeApiError, useApi } from "@/lib/use-api";

type Schedule = {
  key: string;
  task_name: string;
  schedule: string;
  next_run_at: string | null;
  last_success_at: string | null;
  last_failure_at: string | null;
  last_error: string | null;
  status: "ok" | "failing" | "never_run" | "stale";
  runs_24h: number | null;
  failures_24h: number | null;
};

type WorkerHealth = {
  overall: "ok" | "degraded" | "scheduler_stale" | "no_worker_evidence" | "broker_unreachable";
  checked_at: string;
  broker_reachable: boolean | null;
  scheduler: { live: boolean; last_heartbeat_at: string | null; heartbeat_age_seconds: number | null; hostname: string | null };
  worker: { last_ready_at: string | null; hostname: string | null };
  schedules: Schedule[];
  never_run: string[];
  recent_failures: { task_name: string; at: string | null; error: string }[];
};

type SchemaReport = {
  alembic_current: string | null;
  alembic_head: string | null;
  at_head: boolean;
  tables_in_models: number;
  tables_in_db: number;
  blocking_drift: { kind: string; object: string }[];
  other_drift: { kind: string; object: string }[];
  missing_enum_labels: { enum: string; missing: string[] }[];
  ok: boolean;
};

type Task = { id: string; title: string; agent_slug: string; priority: number; status: string };

const OVERALL: Record<WorkerHealth["overall"], { label: string; tone: string; help: string }> = {
  ok: { label: "Operational", tone: "bg-emerald-100 text-emerald-900", help: "Scheduler heartbeat is fresh and no task's latest run failed." },
  degraded: { label: "Degraded", tone: "bg-amber-100 text-amber-900", help: "At least one task's most recent run failed." },
  scheduler_stale: { label: "Scheduler stopped", tone: "bg-red-100 text-red-900", help: "No heartbeat in the last 3 minutes — the worker service is down or Redis is unreachable." },
  no_worker_evidence: {
    label: "No worker running",
    tone: "bg-red-100 text-red-900",
    help: "No heartbeat has ever been recorded. Scheduled tasks are not running in this environment.",
  },
  broker_unreachable: { label: "Redis unreachable", tone: "bg-red-100 text-red-900", help: "The API cannot reach Redis (REDIS_URL)." },
};

const STATUS_TONE: Record<Schedule["status"], string> = {
  ok: "text-emerald-800",
  failing: "text-red-700 font-semibold",
  never_run: "text-slate-500",
  stale: "text-red-700 font-semibold",
};

const STATUS_LABEL: Record<Schedule["status"], string> = {
  ok: "OK",
  failing: "Failing",
  never_run: "Never run",
  stale: "Stale",
};

function when(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-GB", { timeZone: "Europe/London", dateStyle: "short", timeStyle: "short" });
}

export default function SystemHealthPage() {
  const workers = useApi<WorkerHealth>("/api/v1/ops/workers");
  const schema = useApi<SchemaReport>("/api/v1/ops/schema");
  const tasks = useApi<Task[]>("/api/v1/business-director/tasks");
  const [scanError, setScanError] = useState<string | null>(null);

  async function runScan() {
    setScanError(null);
    try {
      await apiPost("/api/v1/business-director/scan", {});
      tasks.reload();
    } catch (e) {
      setScanError(describeApiError(e as Error).detail);
    }
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold text-[#1a1a1a]">System health</h1>
        <p className="mt-1 text-sm text-slate-600">
          Evidence recorded by the running system. A task is only shown as OK after a successful run has actually been recorded.
        </p>
      </header>

      <section aria-labelledby="workers-heading" className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h2 id="workers-heading" className="text-lg font-semibold text-[#1a1a1a]">
            Background jobs &amp; scheduler
          </h2>
          <button type="button" onClick={workers.reload} className="rounded-full border px-3 py-1 text-xs font-medium text-slate-700">
            Refresh
          </button>
        </div>
        <LoadState resource={workers}>
          {(w) => {
            const o = OVERALL[w.overall];
            return (
              <div className="space-y-4">
                <div className="rounded-xl border p-4">
                  <span className={`inline-block rounded-full px-3 py-1 text-sm font-semibold ${o.tone}`} data-testid="worker-overall">
                    {o.label}
                  </span>
                  <p className="mt-2 text-sm text-slate-700">{o.help}</p>
                  <dl className="mt-3 grid grid-cols-1 gap-2 text-sm sm:grid-cols-3">
                    <div>
                      <dt className="text-slate-500">Last scheduler heartbeat</dt>
                      <dd className="font-medium text-[#1a1a1a]">
                        {when(w.scheduler.last_heartbeat_at)}
                        {w.scheduler.heartbeat_age_seconds !== null ? ` (${w.scheduler.heartbeat_age_seconds}s ago)` : ""}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-slate-500">Worker last started</dt>
                      <dd className="font-medium text-[#1a1a1a]">{when(w.worker.last_ready_at)}</dd>
                    </div>
                    <div>
                      <dt className="text-slate-500">Redis (broker)</dt>
                      <dd className="font-medium text-[#1a1a1a]">
                        {w.broker_reachable === null ? "Unknown" : w.broker_reachable ? "Reachable" : "Unreachable"}
                      </dd>
                    </div>
                  </dl>
                  {w.never_run.length > 0 ? (
                    <p className="mt-3 text-xs text-slate-600">
                      {w.never_run.length} scheduled task(s) have never run here, so they are not verified.
                    </p>
                  ) : null}
                </div>

                <div className="overflow-x-auto rounded-xl border">
                  <table className="min-w-full text-left text-sm">
                    <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                      <tr>
                        <th className="px-3 py-2">Task</th>
                        <th className="px-3 py-2">Status</th>
                        <th className="px-3 py-2">Last success</th>
                        <th className="px-3 py-2">Last failure</th>
                        <th className="px-3 py-2">Next run (UK)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {w.schedules.map((s) => (
                        <tr key={s.key} className="border-t align-top">
                          <td className="px-3 py-2 font-medium text-[#1a1a1a]">{s.key}</td>
                          <td className={`px-3 py-2 ${STATUS_TONE[s.status]}`}>{STATUS_LABEL[s.status]}</td>
                          <td className="px-3 py-2 text-slate-700">{when(s.last_success_at)}</td>
                          <td className="px-3 py-2 text-slate-700">
                            {when(s.last_failure_at)}
                            {s.last_error ? <span className="block text-xs text-red-700">{s.last_error}</span> : null}
                          </td>
                          <td className="px-3 py-2 text-slate-700">{when(s.next_run_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-[#1a1a1a]">Recent failures</h3>
                  {w.recent_failures.length === 0 ? (
                    <p className="mt-1 text-sm text-slate-600">No failed runs recorded.</p>
                  ) : (
                    <ul className="mt-2 space-y-2 text-sm">
                      {w.recent_failures.map((f, i) => (
                        <li key={`${f.task_name}-${i}`} className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-red-900">
                          <span className="font-medium">{f.task_name}</span> · {when(f.at)}
                          {f.error ? <span className="block text-xs">{f.error}</span> : null}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            );
          }}
        </LoadState>
      </section>

      <section aria-labelledby="schema-heading" className="space-y-3">
        <h2 id="schema-heading" className="text-lg font-semibold text-[#1a1a1a]">
          Database schema
        </h2>
        <LoadState resource={schema}>
          {(s) => (
            <div className="rounded-xl border p-4 text-sm">
              <p className={s.ok ? "font-semibold text-emerald-800" : "font-semibold text-red-700"} data-testid="schema-status">
                {s.ok ? "Schema matches the application" : "Schema drift detected"}
              </p>
              <p className="mt-1 text-slate-700">
                Migration {s.alembic_current ?? "none recorded"} (latest {s.alembic_head}) · {s.tables_in_db} of {s.tables_in_models} tables
              </p>
              {s.blocking_drift.length > 0 ? (
                <ul className="mt-2 list-disc pl-5 text-red-800">
                  {s.blocking_drift.map((d) => (
                    <li key={`${d.kind}-${d.object}`}>
                      {d.kind.replace("_", " ")}: {d.object}
                    </li>
                  ))}
                </ul>
              ) : null}
              {s.missing_enum_labels.length > 0 ? (
                <p className="mt-2 text-red-800">Missing enum values: {s.missing_enum_labels.map((m) => `${m.enum} (${m.missing.join(", ")})`).join("; ")}</p>
              ) : null}
              {s.other_drift.length > 0 ? (
                <p className="mt-2 text-xs text-slate-500">{s.other_drift.length} non-blocking difference(s) (extra objects in the database).</p>
              ) : null}
            </div>
          )}
        </LoadState>
      </section>

      <section aria-labelledby="tasks-heading" className="space-y-3">
        <h2 id="tasks-heading" className="text-lg font-semibold text-[#1a1a1a]">
          Business Director tasks
        </h2>
        <p className="text-sm text-slate-600">The director scan creates bounded tasks only — it never spends money or contacts customers.</p>
        <button type="button" onClick={runScan} className="rounded-full bg-[#1a1a1a] px-4 py-2 text-sm font-medium text-white">
          Run director scan
        </button>
        {scanError ? (
          <p role="alert" className="text-sm text-red-700">
            {scanError}
          </p>
        ) : null}
        <LoadState resource={tasks} isEmpty={(t) => t.length === 0} empty="No open tasks.">
          {(list) => (
            <ul className="space-y-2 text-sm">
              {list.map((t) => (
                <li key={t.id} className="rounded-lg border px-3 py-2 text-[#1a1a1a]">
                  [{t.priority}] {t.title} → {t.agent_slug}
                </li>
              ))}
            </ul>
          )}
        </LoadState>
      </section>
    </div>
  );
}
