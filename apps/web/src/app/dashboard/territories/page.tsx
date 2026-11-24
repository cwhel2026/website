"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

type Territory = {
  code: string;
  name: string;
  minimum_job_value_gbp: number;
  travel_cost_per_km_gbp: number;
  localities: { name: string }[];
  postcode_districts: { district: string }[];
};

export default function TerritoriesPage() {
  const [territories, setTerritories] = useState<Territory[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Territory[]>("/api/v1/territories")
      .then(setTerritories)
      .catch(() => setError("Could not load territories from API."));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Territory management</h1>
      <p className="mt-2 text-sm text-slate-600">
        Nine configurable operating territories (A–I). Postcode districts and minimum job values are
        administrator-configurable without code changes.
      </p>
      {error && <p className="mt-4 text-sm text-amber-700">{error}</p>}
      <ul className="mt-8 space-y-4">
        {territories.map((t) => (
          <li key={t.code} className="rounded-xl border p-4">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="text-lg font-semibold text-emerald-950">
                {t.code} — {t.name}
              </h2>
              <span className="text-sm text-slate-600">
                Min job £{Number(t.minimum_job_value_gbp).toFixed(2)} · Travel £
                {Number(t.travel_cost_per_km_gbp).toFixed(2)}/km
              </span>
            </div>
            <p className="mt-2 text-xs text-slate-500">
              Postcode districts: {t.postcode_districts.map((d) => d.district).join(", ")}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Towns: {t.localities.map((l) => l.name).join(", ")}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}