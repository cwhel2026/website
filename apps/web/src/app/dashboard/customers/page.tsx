"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPatch } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Customer = {
  id: string;
  full_name: string;
  email: string;
  phone: string | null;
  source: string | null;
  created_at: string;
};

type Enquiry = {
  id: string;
  intention: string | null;
  priority: string;
  callback_status: string;
  callback_preferred_time: string | null;
  callback_outcome: string | null;
  email_delivery: string;
  utm_source: string | null;
  utm_campaign: string | null;
};

const INTENTION_LABELS: Record<string, string> = {
  ready_to_book: "Ready to book",
  callback_requested: "Callback requested",
  estimate_requested: "Estimate requested",
};

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [enquiries, setEnquiries] = useState<Enquiry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [outcome, setOutcome] = useState<Record<string, string>>({});

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Customer[]>("/api/v1/crm/customers", token)
      .then(setCustomers)
      .catch(() => setError("Could not load customers."));
    apiGet<Enquiry[]>("/api/v1/crm/enquiries", token)
      .then(setEnquiries)
      .catch(() => setError("Could not load enquiries."));
  }, []);

  async function saveCallback(enquiry: Enquiry, completed: boolean) {
    const note = (outcome[enquiry.id] || enquiry.callback_outcome || "").trim();
    if (note.length < 2) {
      setError("Add a short note about the callback.");
      return;
    }
    const updated = await apiPatch<Enquiry>(`/api/v1/crm/enquiries/${enquiry.id}/callback`, {
      completed,
      outcome: note,
    });
    setEnquiries((rows) => rows.map((row) => (row.id === updated.id ? { ...row, ...updated } : row)));
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Customers</h1>
      <p className="mt-2 text-sm text-slate-600">CRM records with deduplication by email.</p>
      {error && <p className="mt-4 text-sm text-amber-700">{error}</p>}
      {customers.length === 0 ? (
        <p className="mt-8 text-sm text-slate-500">No customers yet.</p>
      ) : (
        <table className="mt-8 w-full text-left text-sm">
          <thead>
            <tr className="border-b text-slate-500">
              <th className="py-2">Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => (
              <tr key={c.id} className="border-b">
                <td className="py-2 font-medium">{c.full_name}</td>
                <td>{c.email}</td>
                <td>{c.phone ?? "—"}</td>
                <td>{c.source ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h2 className="mt-12 text-xl font-semibold text-emerald-950">Quotation requests</h2>
      <p className="mt-2 text-sm text-slate-600">
        Ready to book, callback requested, or estimate requested. A callback stays open until you record the outcome.
      </p>
      {enquiries.length === 0 ? (
        <p className="mt-6 text-sm text-slate-500">No quotation requests yet.</p>
      ) : (
        <ul className="mt-6 space-y-4">
          {enquiries.map((enquiry) => (
            <li key={enquiry.id} className="rounded-md border p-4 text-sm">
              <p className="font-medium">
                {INTENTION_LABELS[enquiry.intention ?? ""] ?? "Quotation"} · {enquiry.priority}
              </p>
              <p className="mt-1 text-slate-600">
                {enquiry.utm_source ?? "website"}
                {enquiry.utm_campaign ? ` · ${enquiry.utm_campaign}` : ""}
                {enquiry.intention === "estimate_requested" ? ` · email ${enquiry.email_delivery.split("_").join(" ")}` : ""}
              </p>
              {enquiry.intention === "callback_requested" && (
                <div className="mt-3 space-y-2">
                  <p>
                    {enquiry.callback_preferred_time ?? "No time given"} · {enquiry.callback_status.split("_").join(" ")}
                  </p>
                  <label className="block">
                    Outcome
                    <input
                      value={outcome[enquiry.id] ?? enquiry.callback_outcome ?? ""}
                      onChange={(event) =>
                        setOutcome((current) => ({ ...current, [enquiry.id]: event.target.value }))
                      }
                      className="mt-1 w-full rounded-md border px-3 py-2"
                    />
                  </label>
                  <button
                    type="button"
                    className="rounded-md bg-emerald-900 px-3 py-2 text-white"
                    onClick={() => void saveCallback(enquiry, true)}
                  >
                    Mark callback complete
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}