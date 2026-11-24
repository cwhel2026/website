"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Task = { id: string; title: string; agent_slug: string; priority: number; status: string };

export default function SystemHealthPage() {
  const [tasks, setTasks] = useState<Task[]>([]);

  function reload() {
    const token = getToken();
    if (!token) return;
    apiGet<Task[]>("/api/v1/business-director/tasks", token).then(setTasks).catch(() => setTasks([]));
  }

  useEffect(reload, []);

  async function runScan() {
    const token = getToken();
    if (!token) return;
    await apiPost("/api/v1/business-director/scan", {}, token);
    reload();
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">System health & agent tasks</h1>
      <p className="mt-2 text-sm text-slate-600">Business Director scan creates bounded tasks — no autonomous spend.</p>
      <button type="button" onClick={runScan} className="mt-4 rounded-full bg-emerald-900 px-4 py-2 text-sm text-white">
        Run director scan
      </button>
      <ul className="mt-6 space-y-2 text-sm">
        {tasks.length === 0 ? (
          <li className="text-slate-500">No open tasks.</li>
        ) : (
          tasks.map((t) => (
            <li key={t.id} className="rounded border px-3 py-2">
              [{t.priority}] {t.title} → {t.agent_slug}
            </li>
          ))
        )}
      </ul>
    </div>
  );
}