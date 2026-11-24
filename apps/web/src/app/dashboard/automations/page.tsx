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

export default function AutomationsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Agent[]>("/api/v1/automations/agents", token).then(setAgents).catch(() => setAgents([]));
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
      <ul className="mt-6 space-y-2 text-sm">
        {agents.map((a) => (
          <li key={a.slug} className="flex justify-between rounded border px-3 py-2">
            <span>
              <strong>{a.name}</strong> — {a.operating_mode}
            </span>
            <span className="text-slate-500">
              {a.emergency_stop ? "STOPPED" : a.is_paused ? "Paused" : "Active"}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}