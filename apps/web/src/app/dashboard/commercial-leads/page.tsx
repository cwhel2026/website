"use client";

import { LoadState } from "@/components/load-state";
import { useApi } from "@/lib/use-api";

type Lead = {
  id: string;
  business_name: string;
  postcode: string | null;
  category: string | null;
  score: number;
  outreach_status: string;
};

export default function CommercialLeadsPage() {
  const leads = useApi<Lead[]>("/api/v1/marketing/commercial-leads");

  return (
    <div>
      <h1 className="text-2xl font-semibold text-[#1a1a1a]">Commercial leads</h1>
      <p className="mt-2 text-sm text-slate-600">Manual prospecting — PECR/GDPR compliance is checked before any outreach.</p>
      <div className="mt-6 overflow-x-auto">
        <LoadState resource={leads} isEmpty={(l) => l.length === 0} empty="No commercial leads recorded yet.">
          {(list) => (
            <table className="w-full text-left text-sm text-[#1a1a1a]">
              <thead>
                <tr className="border-b text-slate-500">
                  <th className="py-2">Business</th>
                  <th>Score</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {list.map((l) => (
                  <tr key={l.id} className="border-b">
                    <td className="py-2">{l.business_name}</td>
                    <td>{l.score}</td>
                    <td>{l.outreach_status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </LoadState>
      </div>
    </div>
  );
}
