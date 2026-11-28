"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Job = {
  id: string;
  reference: string;
  quotation_id: string | null;
  status: string;
  photo_count: number;
  seven_day_target_date: string | null;
  seven_day_at_risk: boolean | null;
  seven_day_message: string | null;
};

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState<string | null>(null);

  function load() {
    const token = getToken();
    if (!token) return;
    apiGet<Job[]>("/api/v1/jobs", token).then(setJobs).catch(() => setError("Could not load jobs."));
  }
  useEffect(load, []);

  async function action(path: string, body: unknown) {
    try { await apiPost(path, body); setError(null); load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Action failed"); }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950 portal-department-title">Jobs</h1>
      <p className="mt-2 text-sm text-slate-600">Two-stage restoration workflow with seven-day coating targets.</p>
      {error && <p className="mt-4 text-sm text-amber-700">{error}</p>}
      {jobs.length === 0 ? (
        <p className="mt-8 text-sm text-slate-500">No jobs yet. Create from an accepted quotation in the API.</p>
      ) : (
        <ul className="mt-6 space-y-3">
          {jobs.map((j) => (
            <li key={j.reference} className="rounded-lg border p-4 text-sm">
              <div className="font-semibold">{j.reference}</div>
              <div className="text-slate-600">{j.status}</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {j.status === "preparation_scheduled" && <button className="rounded border p-2" onClick={() => { if (window.confirm("Confirm washing is complete?")) void action(`/api/v1/jobs/${j.id}/complete-preparation`, { surface_dry_confirmed: false }); }}>Complete washing</button>}
                {j.status === "coating_scheduled" && <button className="rounded border p-2" onClick={() => { if (window.confirm("Confirm coating is complete, surface was dry and on-site weather was safe?")) void action(`/api/v1/jobs/${j.id}/complete-coating`, { surface_dry_confirmed: true, weather_safe_confirmed: true }); }}>Complete coating</button>}
                {j.status === "completed" && j.quotation_id && <button className="rounded border p-2" onClick={() => void action(`/api/v1/finance/invoices/from-quotation/${j.quotation_id}`, {})}>Create draft invoice</button>}
              </div>
              {j.quotation_id && (
                <div className="text-slate-600">Photographs on the quotation: {j.photo_count ?? 0}</div>
              )}
              {j.seven_day_target_date && (
                <div className={j.seven_day_at_risk ? "text-red-700" : "text-slate-500"}>
                  Coat by {j.seven_day_target_date} — {j.seven_day_message}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}