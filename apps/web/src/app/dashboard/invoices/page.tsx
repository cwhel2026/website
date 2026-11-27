"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { gbp } from "@/lib/format";
import { withLoadError } from "@/lib/load-errors";

type Inv = {
  id: string;
  invoice_number: string;
  status: string;
  total_inc_vat_gbp: number;
  amount_paid_gbp: number;
};

export default function InvoicesPage() {
  const [items, setItems] = useState<Inv[]>([]);

  const [error, setError] = useState<string | null>(null);
  function load() {
    const token = getToken();
    if (!token) return;
    apiGet<Inv[]>("/api/v1/finance/invoices", token).then(setItems).catch(withLoadError(() => setItems([])));
  }
  useEffect(load, []);
  async function payment(i: Inv) {
    const amount = window.prompt("Amount received in GBP");
    if (!amount || !/^\\d+(\\.\\d{1,2})?$/.test(amount) || Number(amount) <= 0) return;
    const reference = window.prompt("Unique bank payment reference");
    if (!reference?.trim()) return;
    if (!window.confirm(`Record £${amount} already received?`)) return;
    try { await apiPost(`/api/v1/finance/invoices/${i.id}/payments`, { amount_gbp: amount, reference }); setError(null); load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Payment recording failed"); }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Invoices</h1>
      {error && <p role="alert">{error}</p>}
      {items.length === 0 ? (
        <p className="mt-8 text-sm text-slate-500">No invoices — create from a quotation via API.</p>
      ) : (
        <table className="mt-6 w-full text-sm">
          <thead>
            <tr className="border-b text-slate-500">
              <th className="py-2 text-left">Number</th>
              <th>Status</th>
              <th>Total</th>
              <th>Paid</th><th>Outstanding</th><th>Action</th>
            </tr>
          </thead>
          <tbody>
            {items.map((i) => (
              <tr key={i.invoice_number} className="border-b">
                <td className="py-2">{i.invoice_number}</td>
                <td>{i.status}</td>
                <td>{gbp(i.total_inc_vat_gbp)}</td>
                <td>{gbp(i.amount_paid_gbp)}</td><td>{gbp(Math.max(0, i.total_inc_vat_gbp - i.amount_paid_gbp))}</td><td>{!['paid', 'void'].includes(i.status) && <button className="rounded border p-2" onClick={() => void payment(i)}>Record payment</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}