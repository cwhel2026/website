"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type FieldJob = {
  reference: string;
  status: string;
  postcode: string | null;
  next_appointment_type: string | null;
  next_appointment_start: string | null;
  tasks: string[];
};

export default function FieldPage() {
  const [jobs, setJobs] = useState<FieldJob[]>([]);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<FieldJob[]>("/api/v1/jobs/field/today", token).then(setJobs).catch(() => setJobs([]));
  }, []);

  return (
    <div className="max-w-md">
      <h1 className="text-xl font-semibold text-emerald-950">Today&apos;s jobs</h1>
      <p className="text-sm text-slate-600">Mobile field view — quick actions wire to API in a follow-up.</p>
      {jobs.length === 0 ? (
        <p className="mt-8 text-sm text-slate-500">No jobs today.</p>
      ) : (
        jobs.map((j) => (
          <article key={j.reference} className="mt-4 rounded-xl border-2 border-emerald-900/20 bg-emerald-50/30 p-4">
            <h2 className="font-bold text-emerald-950">{j.reference}</h2>
            <p className="text-sm">
              {j.next_appointment_type} · {j.postcode ?? "—"}
            </p>
            {j.next_appointment_start && (
              <p className="text-sm text-slate-600">
                {new Date(j.next_appointment_start).toLocaleTimeString("en-GB", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            )}
            <ul className="mt-3 list-disc pl-5 text-sm">
              {j.tasks.map((t) => (
                <li key={t}>{t}</li>
              ))}
            </ul>
            <div className="mt-4 flex flex-wrap gap-2">
              <button type="button" className="rounded-lg bg-emerald-900 px-4 py-3 text-sm font-semibold text-white">
                Start work
              </button>
              <button type="button" className="rounded-lg border px-4 py-3 text-sm">
                Upload photos
              </button>
            </div>
          </article>
        ))
      )}
    </div>
  );
}