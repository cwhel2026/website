"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Quotation = { reference: string; total_inc_vat_gbp: number; status: string; created_at: string };
type Enquiry = { id: string; stage: string; created_at: string };

export default function DashboardOverviewPage() {
  const [quotes, setQuotes] = useState<Quotation[]>([]);
  const [enquiries, setEnquiries] = useState<Enquiry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    Promise.all([
      apiGet<Quotation[]>("/api/v1/quotations", token),
      apiGet<Enquiry[]>("/api/v1/crm/enquiries", token),
    ])
      .then(([q, e]) => {
        setQuotes(q.slice(0, 5));
        setEnquiries(e.slice(0, 5));
      })
      .catch(() => setError("Could not load dashboard data — is the API running?"));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Overview</h1>
      <p className="mt-2 text-sm text-slate-600">
        Genuine records only — empty states shown when no data exists.
      </p>

      {error && <p className="mt-4 text-sm text-amber-700">{error}</p>}

      <div className="mt-8 grid gap-6 md:grid-cols-2">
        <section>
          <h2 className="font-semibold text-emerald-900">Recent quotations</h2>
          {quotes.length === 0 ? (
            <p className="mt-3 text-sm text-slate-500">No quotations yet.</p>
          ) : (
            <ul className="mt-3 space-y-2 text-sm">
              {quotes.map((q) => (
                <li key={q.reference} className="rounded-lg border px-3 py-2">
                  {q.reference} · £{Number(q.total_inc_vat_gbp).toFixed(2)} · {q.status}
                </li>
              ))}
            </ul>
          )}
        </section>
        <section>
          <h2 className="font-semibold text-emerald-900">Recent enquiries</h2>
          {enquiries.length === 0 ? (
            <p className="mt-3 text-sm text-slate-500">No enquiries yet.</p>
          ) : (
            <ul className="mt-3 space-y-2 text-sm">
              {enquiries.map((e) => (
                <li key={e.id} className="rounded-lg border px-3 py-2">
                  {e.stage} · {new Date(e.created_at).toLocaleString("en-GB")}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}