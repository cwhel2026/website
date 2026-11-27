"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPatch } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Line = { label: string; amount_gbp?: number };

type PhotoReview = {
  id: string;
  quotation_reference: string | null;
  quotation_total_gbp: string | null;
  photo_count: number;
  ai_status: string;
  ai_summary: string | null;
  review_required: boolean;
  review_status: string;
  repair_price_gbp: string | null;
  marketing_use_allowed: boolean;
};

type Quotation = {
  reference: string;
  status: string;
  total_inc_vat_gbp: number;
  subtotal_ex_vat_gbp: number;
  vat_gbp: number;
  vat_charged: boolean;
  total_area_sqm: number;
  meets_minimum_margin: boolean;
  requires_approval: boolean;
  created_at: string;
  breakdown?: { lines?: Line[] } | null;
};

export default function QuotationsPage() {
  const [quotes, setQuotes] = useState<Quotation[]>([]);
  const [reviews, setReviews] = useState<PhotoReview[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [prices, setPrices] = useState<Record<string, string>>({});
  const [notes, setNotes] = useState<Record<string, string>>({});

  function load() {
    const token = getToken();
    if (!token) return;
    apiGet<Quotation[]>("/api/v1/quotations", token)
      .then(setQuotes)
      .catch(() => setError("Could not load quotations."));
    apiGet<PhotoReview[]>("/api/v1/quotation-photos/admin/reviews", token)
      .then(setReviews)
      .catch(() => setReviews([]));
  }

  useEffect(() => {
    load();
  }, []);

  async function saveRepair(review: PhotoReview) {
    const token = getToken();
    if (!token) return;
    const raw = (prices[review.id] ?? review.repair_price_gbp ?? "").trim();
    const note = (notes[review.id] ?? "").trim();
    if (note.length < 2) {
      setError("Add a short note before saving the repair price.");
      return;
    }
    await apiPatch(
      `/api/v1/quotation-photos/admin/sets/${review.id}/repair`,
      {
        repair_price_gbp: raw ? Number(raw) : null,
        repair_note: note,
        approved: true,
      },
      token,
    );
    setError(null);
    load();
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Quotations</h1>
      <p className="mt-2 text-sm text-slate-600">
        Customer totals, with the internal costing breakdown kept here for audit.
      </p>
      {error && <p className="mt-4 text-sm text-amber-700">{error}</p>}
      {reviews.length > 0 && (
        <section className="mt-10">
          <h2 className="text-lg font-semibold text-emerald-950">Photograph review</h2>
          <p className="mt-1 text-sm text-slate-600">
            A repair price here is separate from the estimate. Saving it does not change the quotation total.
          </p>
          <ul className="mt-4 space-y-4">
            {reviews.map((review) => (
              <li key={review.id} className="rounded-lg border p-4 text-sm">
                <p className="font-medium">
                  {review.quotation_reference ?? "Not linked yet"} · {review.photo_count} photograph
                  {review.photo_count === 1 ? "" : "s"}
                  {review.quotation_total_gbp ? ` · estimate £${review.quotation_total_gbp}` : ""}
                </p>
                <p className="mt-1 text-slate-600">
                  Assessment: {review.ai_status}
                  {review.review_required ? " · flagged for review" : ""}
                  {review.review_status === "approved" ? " · repair price approved" : ""}
                </p>
                {review.ai_summary && <p className="mt-1 text-slate-600">{review.ai_summary}</p>}
                {review.marketing_use_allowed ? null : (
                  <p className="mt-1 text-slate-500">Not approved for marketing.</p>
                )}
                <div className="mt-3 flex flex-wrap items-end gap-2">
                  <label className="text-xs">
                    Repair price £
                    <input
                      value={prices[review.id] ?? review.repair_price_gbp ?? ""}
                      onChange={(event) => setPrices((current) => ({ ...current, [review.id]: event.target.value }))}
                      className="mt-1 block w-28 rounded border px-2 py-1"
                    />
                  </label>
                  <label className="text-xs">
                    Note
                    <input
                      value={notes[review.id] ?? ""}
                      onChange={(event) => setNotes((current) => ({ ...current, [review.id]: event.target.value }))}
                      className="mt-1 block w-64 rounded border px-2 py-1"
                    />
                  </label>
                  <button type="button" className="rounded bg-emerald-900 px-3 py-1.5 text-white" onClick={() => void saveRepair(review)}>
                    Save repair price
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
      {quotes.length === 0 ? (
        <p className="mt-8 text-sm text-slate-500">No quotations yet.</p>
      ) : (
        <table className="mt-8 w-full text-left text-sm">
          <thead>
            <tr className="border-b text-slate-500">
              <th className="py-2">Reference</th>
              <th>Status</th>
              <th>Customer total</th>
              <th>Area (m²)</th>
              <th>Approval</th>
            </tr>
          </thead>
          <tbody>
            {quotes.map((q) => (
              <tr key={q.reference} className="border-b">
                <td className="py-2 font-medium">{q.reference}</td>
                <td>{q.status}</td>
                <td>
                  £{Number(q.total_inc_vat_gbp).toFixed(2)}
                  {q.vat_charged ? " inc. VAT" : ""}
                  {q.breakdown?.lines && q.breakdown.lines.length > 0 ? (
                    <details className="mt-1 text-xs text-slate-600">
                      <summary>Internal breakdown</summary>
                      <ul className="mt-1 space-y-0.5">
                        {q.breakdown.lines.map((line) => (
                          <li key={line.label} className="flex justify-between gap-4">
                            <span>{line.label}</span>
                            <span>{line.amount_gbp != null ? `£${Number(line.amount_gbp).toFixed(2)}` : ""}</span>
                          </li>
                        ))}
                      </ul>
                    </details>
                  ) : null}
                </td>
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