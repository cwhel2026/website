"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Lead = {
  id: string;
  business_name: string;
  postcode: string | null;
  category: string | null;
  score: number;
  outreach_status: string;
};

export default function CommercialLeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);

  function reload() {
    const token = getToken();
    if (!token) return;
    apiGet<Lead[]>("/api/v1/marketing/commercial-leads", token).then(setLeads).catch(() => setLeads([]));
  }

  useEffect(reload, []);

  async function addSample() {
    const token = getToken();
    if (!token) return;
    await apiPost(
      "/api/v1/marketing/commercial-leads",
      {
        business_name: "Sample Retail Park Ltd",
        postcode: "PR1 1AA",
        town: "Preston",
        category: "Retail car park",
        contact_email: "facilities@example.com",
      },
      token,
    );
    reload();
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Commercial leads</h1>
      <p className="mt-2 text-sm text-slate-600">Manual prospecting — PECR/GDPR compliance before outreach.</p>
      <button type="button" onClick={addSample} className="mt-4 rounded border px-4 py-2 text-sm">
        Add sample lead
      </button>
      <table className="mt-6 w-full text-left text-sm">
        <thead>
          <tr className="border-b text-slate-500">
            <th className="py-2">Business</th>
            <th>Score</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((l) => (
            <tr key={l.id} className="border-b">
              <td className="py-2">{l.business_name}</td>
              <td>{l.score}</td>
              <td>{l.outreach_status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}