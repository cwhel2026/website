"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Job = {
  reference: string;
  status: string;
  seven_day_target_date: string | null;
  seven_day_at_risk: boolean | null;
  seven_day_message: string | null;
};

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Job[]>("/api/v1/jobs", token).then(setJobs).catch(() => setError("Could not load jobs."));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Jobs</h1>
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