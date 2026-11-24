"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Job = {
  reference: string;
  status: string;
  drying_status: string;
  seven_day_target_date: string | null;
  seven_day_at_risk: boolean | null;
};

export default function WashPendingPage() {
  const [jobs, setJobs] = useState<Job[]>([]);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Job[]>("/api/v1/jobs/wash-pending-coat", token).then(setJobs).catch(() => setJobs([]));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Washed — awaiting coating</h1>
      <p className="mt-2 text-sm text-slate-600">Priority queue by seven-day target and weather windows.</p>
      {jobs.length === 0 ? (
        <p className="mt-8 text-sm text-slate-500">No driveways awaiting coating.</p>
      ) : (
        <ul className="mt-6 space-y-3">
          {jobs.map((j) => (
            <li
              key={j.reference}
              className={`rounded-lg border p-4 text-sm ${j.seven_day_at_risk ? "border-red-300 bg-red-50" : ""}`}
            >
              <div className="font-semibold">{j.reference}</div>
              <div>Drying: {j.drying_status}</div>
              {j.seven_day_target_date && <div>Target date: {j.seven_day_target_date}</div>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}