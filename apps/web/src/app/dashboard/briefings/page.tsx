"use client";

import { useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Briefing = {
  kind: string;
  content: Record<string, unknown>;
  generated_at: string;
};

export default function BriefingsPage() {
  const [morning, setMorning] = useState<Briefing | null>(null);
  const [evening, setEvening] = useState<Briefing | null>(null);

  async function generate(kind: "morning" | "evening") {
    const token = getToken();
    if (!token) return;
    const b = await apiPost<Briefing>(`/api/v1/briefings/generate/${kind}`, {}, token);
    if (kind === "morning") setMorning(b);
    else setEvening(b);
  }

  async function loadLatest() {
    const token = getToken();
    if (!token) return;
    try {
      setMorning(await apiGet<Briefing>("/api/v1/briefings/latest/morning", token));
    } catch {
      setMorning(null);
    }
    try {
      setEvening(await apiGet<Briefing>("/api/v1/briefings/latest/evening", token));
    } catch {
      setEvening(null);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Daily briefings</h1>
      <p className="mt-2 text-sm text-slate-600">Generated from real diary, weather simulation, and approval data.</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <button type="button" onClick={() => generate("morning")} className="rounded-full bg-emerald-900 px-4 py-2 text-sm text-white">
          Generate morning
        </button>
        <button type="button" onClick={() => generate("evening")} className="rounded-full bg-emerald-900 px-4 py-2 text-sm text-white">
          Generate evening
        </button>
        <button type="button" onClick={loadLatest} className="rounded-full border px-4 py-2 text-sm">
          Load latest
        </button>
      </div>
      {[{ label: "Morning", data: morning }, { label: "Evening", data: evening }].map(({ label, data }) => (
        <section key={label} className="mt-6">
          <h2 className="font-semibold">{label}</h2>
          {data ? (
            <pre className="mt-2 max-h-64 overflow-auto rounded border bg-slate-50 p-3 text-xs">
              {JSON.stringify(data.content, null, 2)}
            </pre>
          ) : (
            <p className="mt-2 text-sm text-slate-500">Not generated yet.</p>
          )}
        </section>
      ))}
    </div>
  );
}