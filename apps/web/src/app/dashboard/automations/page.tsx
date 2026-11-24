"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Agent = {
  slug: string;
  name: string;
  operating_mode: string;
  is_paused: boolean;
  emergency_stop: boolean;
};

type WorkerTask = {
  task_name: string;
  description: string;
  last_status: string;
  last_success_at: string | null;
  recent_error: string | null;
};

export default function AutomationsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [workers, setWorkers] = useState<WorkerTask[]>([]);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Agent[]>("/api/v1/automations/agents", token).then(setAgents).catch(() => setAgents([]));
    apiGet<{ tasks: WorkerTask[] }>("/api/v1/automations/workers/runs", token)
      .then((d) => setWorkers(d.tasks))
      .catch(() => setWorkers([]));
  }, []);

  async function emergencyStop() {
    const token = getToken();
    if (!token) return;
    await apiPost("/api/v1/automations/emergency-stop", {}, token);
    window.location.reload();
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Automations & agents</h1>
      <p className="mt-2 text-sm text-slate-600">Default mode: supervised. Marketing and ad spend require approval.</p>
      <button
        type="button"
        onClick={emergencyStop}
        className="mt-4 rounded border border-red-400 px-4 py-2 text-sm text-red-800"
      >
        Emergency stop all agents
      </button>
      <h2 className="mt-10 text-lg font-semibold text-asphalt">Background workers</h2>
      <p className="text-sm text-asphalt/70">Last run status from the database — not fabricated agent activity.</p>
      <ul className="mt-4 space-y-2 text-sm">
        {workers.map((w) => (
          <li key={w.task_name} className="rounded border border-stone-line px-3 py-2">
            <div className="flex justify-between gap-2">
              <strong>{w.task_name}</strong>
              <span className="text-xs uppercase text-asphalt/60">{w.last_status}</span>
            </div>
            <p className="text-xs text-asphalt/60">{w.description}</p>
            {w.last_success_at && (
              <p className="text-xs text-restore-dark">Last success: {new Date(w.last_success_at).toLocaleString("en-GB")}</p>
            )}
            {w.recent_error && <p className="text-xs text-red-700">{w.recent_error}</p>}
          </li>
        ))}
      </ul>

      <h2 className="mt-10 text-lg font-semibold text-asphalt">Agent profiles</h2>
      <ul className="mt-4 space-y-2 text-sm">
        {agents.map((a) => (
          <li key={a.slug} className="flex justify-between rounded border border-stone-line px-3 py-2">
            <span>
              <strong>{a.name}</strong> — {a.operating_mode}
            </span>
            <span className="text-asphalt/50">
              {a.emergency_stop ? "STOPPED" : a.is_paused ? "Paused" : "Active"}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}