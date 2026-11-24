"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Quotation = {
  reference: string;
  status: string;
  total_inc_vat_gbp: number;
  total_area_sqm: number;
  meets_minimum_margin: boolean;
  requires_approval: boolean;
  created_at: string;
};

export default function QuotationsPage() {
  const [quotes, setQuotes] = useState<Quotation[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Quotation[]>("/api/v1/quotations", token)
      .then(setQuotes)
      .catch(() => setError("Could not load quotations."));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Quotations</h1>
      <p className="mt-2 text-sm text-slate-600">
        Versioned calculations with approval routing for complex or low-margin jobs.
      </p>
      {error && <p className="mt-4 text-sm text-amber-700">{error}</p>}
      {quotes.length === 0 ? (
        <p className="mt-8 text-sm text-slate-500">No quotations yet.</p>
      ) : (
        <table className="mt-8 w-full text-left text-sm">
          <thead>
            <tr className="border-b text-slate-500">
              <th className="py-2">Reference</th>
              <th>Status</th>
              <th>Total inc VAT</th>
              <th>Area (m²)</th>
              <th>Approval</th>
            </tr>
          </thead>
          <tbody>
            {quotes.map((q) => (
              <tr key={q.reference} className="border-b">
                <td className="py-2 font-medium">{q.reference}</td>
                <td>{q.status}</td>
                <td>£{Number(q.total_inc_vat_gbp).toFixed(2)}</td>
                <td>{Number(q.total_area_sqm).toFixed(1)}</td>
                <td>{q.requires_approval ? "Required" : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}