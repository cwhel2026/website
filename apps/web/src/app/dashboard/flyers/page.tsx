"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Flyer = { id: string; name: string; qr_slug: string; status: string; quantity: number };

export default function FlyersPage() {
  const [flyers, setFlyers] = useState<Flyer[]>([]);

  function reload() {
    const token = getToken();
    if (!token) return;
    apiGet<Flyer[]>("/api/v1/marketing/flyers", token).then(setFlyers).catch(() => setFlyers([]));
  }

  useEffect(reload, []);

  async function createFlyer() {
    const token = getToken();
    if (!token) return;
    const res = await apiPost<{ qr_slug: string; landing_path: string }>(
      "/api/v1/marketing/flyers",
      {
        name: "Ormskirk spring drop",
        postcode_targets: "L39, L40",
        quantity: 2000,
        print_cost_gbp: 180,
        distribution_cost_gbp: 120,
      },
      token,
    );
    alert(`QR landing: ${res.landing_path}`);
    reload();
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Flyer campaigns</h1>
      <p className="mt-2 text-sm text-slate-600">Unique QR codes per campaign — order pack for manual print/distribution.</p>
      <button type="button" onClick={createFlyer} className="mt-4 rounded-full bg-emerald-900 px-4 py-2 text-sm text-white">
        New flyer campaign
      </button>
      <ul className="mt-6 space-y-2 text-sm">
        {flyers.map((f) => (
          <li key={f.id} className="rounded border px-3 py-2">
            {f.name} · {f.quantity} units · /c/{f.qr_slug} · {f.status}
          </li>
        ))}
      </ul>
    </div>
  );
}