"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { gbp } from "@/lib/format";
import { withLoadError } from "@/lib/load-errors";

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
    apiGet<Inv[]>("/api/v1/finance/invoices", token).then(setItems).catch(withLoadError(() => setItems([])));
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
                <td>{gbp(i.total_inc_vat_gbp)}</td>
                <td>{gbp(i.amount_paid_gbp)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}