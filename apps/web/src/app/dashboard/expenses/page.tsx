"use client";

import { LoadState } from "@/components/load-state";
import { useApi } from "@/lib/use-api";

type Exp = { description: string; category: string; amount_gbp: number; expense_date: string };

export default function ExpensesPage() {
  const items = useApi<Exp[]>("/api/v1/finance/expenses");

  return (
    <div>
      <h1 className="text-2xl font-semibold text-[#1a1a1a]">Expenses</h1>
      <p className="mt-2 text-sm text-slate-600">
        Expenses recorded from receipts (Telegram) and FreeAgent. Nothing here is created automatically for testing.
      </p>
      <div className="mt-6">
        <LoadState resource={items} isEmpty={(i) => i.length === 0} empty="No expenses recorded yet.">
          {(list) => (
            <ul className="space-y-2 text-sm">
              {list.map((e, i) => (
                <li key={`${e.description}-${i}`} className="rounded-lg border px-3 py-2 text-[#1a1a1a]">
                  {e.expense_date} · {e.description} · £{Number(e.amount_gbp).toFixed(2)} ({e.category})
                </li>
              ))}
            </ul>
          )}
        </LoadState>
      </div>
    </div>
  );
}
