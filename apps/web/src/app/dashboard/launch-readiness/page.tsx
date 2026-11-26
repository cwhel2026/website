"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { withLoadError } from "@/lib/load-errors";

type Readiness = {
  pre_launch: boolean;
  ready_score: number;
  ready_total: number;
  external_blockers: string[];
  message: string;
  items: Array<{ key: string; label: string; status: string }>;
};

export default function LaunchReadinessPage() {
  const [data, setData] = useState<Readiness | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Readiness>("/api/v1/marketing/launch/readiness", token).then(setData).catch(withLoadError(() => setData(null)));
  }, []);

  const pauseAll = async () => {
    const token = getToken();
    if (!token) return;
    await apiPost("/api/v1/marketing/launch/pause-all-advertising", {}, token);
  };

  return (
    <div className="max-w-2xl space-y-6 pb-20">
      <h1 className="text-2xl font-semibold text-emerald-950">Pre-launch control centre</h1>
      <p className="text-sm text-slate-600">
        You can use research, content studio and prospects before Facebook or ad accounts exist.
      </p>
      {data && (
        <>
          <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm">{data.message}</p>
          <p className="text-sm">
            Readiness: {data.ready_score}/{data.ready_total} · Pre-launch: {data.pre_launch ? "yes" : "no"}
          </p>
          <ul className="space-y-2 text-sm">
            {data.items.map((i) => (
              <li key={i.key} className="flex justify-between rounded border px-3 py-2">
                <span>{i.label}</span>
                <span className="text-slate-600">{i.status.replace(/_/g, " ")}</span>
              </li>
            ))}
          </ul>
          {data.external_blockers.length > 0 && (
            <section>
              <h2 className="font-semibold text-amber-800">Before go-live</h2>
              <ul className="list-disc pl-5 text-sm text-amber-900">
                {data.external_blockers.map((b) => (
                  <li key={b}>{b}</li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}
      <button type="button" onClick={pauseAll} className="w-full rounded-lg bg-red-800 py-2 text-white">
        Emergency pause all advertising
      </button>
      <nav className="grid grid-cols-2 gap-2 text-sm">
        <Link href="/dashboard/marketing-integrations" className="rounded border px-3 py-2 text-center">
          Integration setup
        </Link>
        <Link href="/dashboard/marketing-hub" className="rounded border px-3 py-2 text-center">
          Marketing hub
        </Link>
        <Link href="/dashboard/content-studio" className="rounded border px-3 py-2 text-center">
          Content studio
        </Link>
        <Link href="/dashboard/content-calendar" className="rounded border px-3 py-2 text-center">
          Content calendar
        </Link>
      </nav>
    </div>
  );
}