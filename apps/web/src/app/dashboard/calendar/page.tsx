"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Appt = {
  job_reference: string;
  appointment_type: string;
  scheduled_start: string;
  scheduled_end: string;
  postcode: string | null;
};

export default function CalendarPage() {
  const [items, setItems] = useState<Appt[]>([]);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    const from = new Date();
    from.setHours(0, 0, 0, 0);
    const to = new Date();
    to.setDate(to.getDate() + 14);
    const q = `from=${from.toISOString()}&to=${to.toISOString()}`;
    apiGet<Appt[]>(`/api/v1/calendar/appointments?${q}`, token).then(setItems).catch(() => setItems([]));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Calendar</h1>
      <p className="mt-2 text-sm text-slate-600">Next 14 days — authoritative internal calendar.</p>
      {items.length === 0 ? (
        <p className="mt-8 text-sm text-slate-500">No appointments scheduled.</p>
      ) : (
        <ul className="mt-6 space-y-2 text-sm">
          {items.map((a, i) => (
            <li key={`${a.job_reference}-${i}`} className="rounded border px-3 py-2">
              <span className="font-medium">{a.job_reference}</span> · {a.appointment_type} ·{" "}
              {new Date(a.scheduled_start).toLocaleString("en-GB")}
              {a.postcode ? ` · ${a.postcode}` : ""}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}