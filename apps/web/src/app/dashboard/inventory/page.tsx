"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Stock = { sku: string; name: string; quantity_on_hand: number; reorder_level: number; unit: string };

export default function InventoryPage() {
  const [items, setItems] = useState<Stock[]>([]);
  const [forecast, setForecast] = useState<{ needs: Array<{ stock_name: string; quantity_needed: number; unit: string }>; low_stock: unknown[] } | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Stock[]>("/api/v1/inventory/items", token).then(setItems).catch(() => setItems([]));
    apiGet<typeof forecast>("/api/v1/inventory/forecast?days=7", token).then(setForecast).catch(() => setForecast(null));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Inventory</h1>
      <p className="mt-2 text-sm text-slate-600">Coverage rates are configurable — verify with manufacturer data.</p>
      {forecast && forecast.low_stock.length > 0 && (
        <p className="mt-4 text-sm text-amber-800">Low stock alerts: {forecast.low_stock.length}</p>
      )}
      {forecast && forecast.needs.length > 0 && (
        <p className="mt-2 text-sm">
          Next 7 days coating need: {forecast.needs[0].quantity_needed} {forecast.needs[0].unit} ({forecast.needs[0].stock_name})
        </p>
      )}
      <table className="mt-6 w-full text-sm">
        <thead>
          <tr className="border-b text-slate-500">
            <th className="py-2 text-left">SKU</th>
            <th>On hand</th>
            <th>Reorder</th>
          </tr>
        </thead>
        <tbody>
          {items.map((s) => (
            <tr key={s.sku} className="border-b">
              <td className="py-2">{s.name}</td>
              <td>
                {s.quantity_on_hand} {s.unit}
              </td>
              <td>{s.reorder_level}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}