"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Inv = {
  invoice_number: string;
  status: string;
  total_inc_vat_gbp: number;
  amount_paid_gbp: number;
};

export default function InvoicesPage() {
  const [items, setItems] = useState<Inv[]>([]);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Inv[]>("/api/v1/finance/invoices", token).then(setItems).catch(() => setItems([]));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Invoices</h1>
      {items.length === 0 ? (
        <p className="mt-8 text-sm text-slate-500">No invoices — create from a quotation via API.</p>
      ) : (
        <table className="mt-6 w-full text-sm">
          <thead>
            <tr className="border-b text-slate-500">
              <th className="py-2 text-left">Number</th>
              <th>Status</th>
              <th>Total</th>
              <th>Paid</th>
            </tr>
          </thead>
          <tbody>
            {items.map((i) => (
              <tr key={i.invoice_number} className="border-b">
                <td className="py-2">{i.invoice_number}</td>
                <td>{i.status}</td>
                <td>£{i.total_inc_vat_gbp.toFixed(2)}</td>
                <td>£{i.amount_paid_gbp.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}