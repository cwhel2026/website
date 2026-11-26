"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { withLoadError } from "@/lib/load-errors";

type Cal = {
  days: Record<string, Array<{ platform: string; title: string; status: string }>>;
  unscheduled_drafts: Array<{ platform: string; title: string; status: string }>;
};

export default function ContentCalendarPage() {
  const [data, setData] = useState<Cal | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Cal>("/api/v1/marketing/content/calendar", token).then(setData).catch(withLoadError(() => setData(null)));
  }, []);

  return (
    <div className="max-w-2xl space-y-4 pb-16">
      <h1 className="text-2xl font-semibold">Content calendar</h1>
      <p className="text-sm text-slate-600">Scheduled posts appear by day. Unscheduled drafts stay internal until approved.</p>
      {data?.unscheduled_drafts && data.unscheduled_drafts.length > 0 && (
        <section>
          <h2 className="font-semibold text-sm">Drafts / approval queue</h2>
          <ul className="mt-2 space-y-1 text-sm">
            {data.unscheduled_drafts.map((d, i) => (
              <li key={i}>
                {d.platform} — {d.title} ({d.status})
              </li>
            ))}
          </ul>
        </section>
      )}
      {data &&
        Object.entries(data.days).map(([day, items]) => (
          <section key={day}>
            <h2 className="font-semibold">{day}</h2>
            <ul className="text-sm">
              {items.map((d, i) => (
                <li key={i}>
                  {d.platform} — {d.title} ({d.status})
                </li>
              ))}
            </ul>
          </section>
        ))}
    </div>
  );
}