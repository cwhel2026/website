"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Approval = {
  id: string;
  approval_type: string;
  title: string;
  summary: string | null;
  status: string;
};

export default function ApprovalsPage() {
  const [items, setItems] = useState<Approval[]>([]);

  function reload() {
    const token = getToken();
    if (!token) return;
    apiGet<Approval[]>("/api/v1/approvals", token).then(setItems).catch(() => setItems([]));
  }

  useEffect(reload, []);

  async function decide(id: string, action: "approve" | "reject") {
    const token = getToken();
    if (!token) return;
    await apiPost(`/api/v1/approvals/${id}/${action}`, { note: "" }, token);
    reload();
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Approval centre</h1>
      <p className="mt-2 text-sm text-slate-600">Quotations, messages and other supervised actions.</p>
      {items.length === 0 ? (
        <p className="mt-8 text-sm text-slate-500">No pending approvals.</p>
      ) : (
        <ul className="mt-6 space-y-3">
          {items.map((a) => (
            <li key={a.id} className="rounded-lg border p-4 text-sm">
              <div className="font-semibold">{a.title}</div>
              <div className="text-slate-600">{a.approval_type}</div>
              {a.summary && <p className="mt-2 text-slate-700">{a.summary}</p>}
              <div className="mt-3 flex gap-2">
                <button
                  type="button"
                  onClick={() => decide(a.id, "approve")}
                  className="rounded bg-emerald-800 px-3 py-1 text-white"
                >
                  Approve
                </button>
                <button
                  type="button"
                  onClick={() => decide(a.id, "reject")}
                  className="rounded border px-3 py-1"
                >
                  Reject
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}