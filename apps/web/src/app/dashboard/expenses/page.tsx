"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Exp = { description: string; category: string; amount_gbp: number; expense_date: string };

export default function ExpensesPage() {
  const [items, setItems] = useState<Exp[]>([]);

  function reload() {
    const token = getToken();
    if (!token) return;
    apiGet<Exp[]>("/api/v1/finance/expenses", token).then(setItems).catch(() => setItems([]));
  }

  useEffect(reload, []);

  async function addSample() {
    const token = getToken();
    if (!token) return;
    await apiPost(
      "/api/v1/finance/expenses",
      { description: "Fuel — regional run", category: "fuel", amount_gbp: 45.5 },
      token,
    );
    reload();
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Expenses</h1>
      <button type="button" onClick={addSample} className="mt-4 rounded border px-4 py-2 text-sm">
        Add sample expense
      </button>
      <ul className="mt-6 space-y-2 text-sm">
        {items.map((e, i) => (
          <li key={`${e.description}-${i}`} className="rounded border px-3 py-2">
            {e.expense_date} · {e.description} · £{e.amount_gbp.toFixed(2)} ({e.category})
          </li>
        ))}
      </ul>
    </div>
  );
}