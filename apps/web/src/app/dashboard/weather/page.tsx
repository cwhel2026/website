"use client";

import { useState } from "react";
import { apiGet } from "@/lib/api";

type Hour = {
  forecast_time: string;
  temp_c: number;
  precip_probability_pct: number;
  wind_mph: number;
};

export default function WeatherPage() {
  const [rows, setRows] = useState<Hour[]>([]);
  const postcode = "L39 4RX";

  async function load() {
    // Burscough default until geocoding is integrated
    const data = await apiGet<Hour[]>("/api/v1/weather/forecast?lat=53.5977&lon=-2.8407&hours=24");
    setRows(data);
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-emerald-950">Weather intelligence</h1>
      <p className="mt-2 text-sm text-slate-600">
        Simulation mode for development — labelled clearly, not live MET data. Postcode: {postcode}
      </p>
      <button
        type="button"
        onClick={() => load()}
        className="mt-4 rounded-full bg-emerald-900 px-4 py-2 text-sm text-white"
      >
        Load 24h Burscough simulation
      </button>
      <ul className="mt-6 max-h-96 overflow-y-auto text-xs">
        {rows.map((r) => (
          <li key={r.forecast_time} className="border-b py-1">
            {new Date(r.forecast_time).toLocaleString("en-GB")} · {r.temp_c}°C · rain {r.precip_probability_pct}% ·
            wind {r.wind_mph} mph
          </li>
        ))}
      </ul>
    </div>
  );
}