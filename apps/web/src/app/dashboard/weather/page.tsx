"use client";

import { useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";

type Hour = {
  forecast_time: string;
  temp_c: number;
  precip_probability_pct: number;
  wind_mph: number;
  source: string;
  is_live: boolean;
};

export default function WeatherPage() {
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const [rows, setRows] = useState<Hour[]>([]);
  const [postcode, setPostcode] = useState("L39 4RX");
  const [status, setStatus] = useState<string | null>(null);

  async function load() {
    setBusy(true);setError("");setRows([]);setStatus(null);
    try {
    const token = getToken();
    const meta = await apiGet<{ provider: string; simulation_allowed_for_booking: boolean }>(
      "/api/v1/weather/status",
      token ?? undefined,
    );
    setStatus(`${meta.provider} · booking simulation ${meta.simulation_allowed_for_booking ? "allowed" : "blocked"}`);
    const data = await apiGet<Hour[]>(
      `/api/v1/weather/forecast?postcode=${encodeURIComponent(postcode)}&hours=24`,
      token ?? undefined,
    );
    setRows(data);
    } catch {setError("Forecast unavailable. Do not use this page to confirm a booking.");} finally {setBusy(false);}
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-semibold text-asphalt portal-department-title">Weather intelligence</h1>
      <p className="mt-2 text-sm text-asphalt/70">
        Live UK forecasts via Open-Meteo when available. Simulation is labelled and never used for booking checks in
        production.
      </p>
      {status && <p className="mt-2 text-xs text-restore-dark">{status}</p>}
      <label className="mt-4 block text-sm">
        Postcode
        <input
          value={postcode}
          onChange={(e) => setPostcode(e.target.value.toUpperCase())}
          className="mt-1 w-full rounded border px-3 py-2"
        />
      </label>
      <button type="button" disabled={busy} onClick={() => load()} className="btn-primary mt-4">
        {busy?"Loading…":"Load 24h forecast"}
      </button>
      {error&&<p role="alert" className="mt-3 text-red-700">{error}</p>}
      {rows[0] && (
        <p className="mt-3 text-xs text-asphalt/60">
          Source: {rows[0].source} · live data: {rows[0].is_live ? "yes" : "no (simulation)"}
        </p>
      )}
      <ul className="mt-6 max-h-96 overflow-y-auto text-xs">
        {rows.map((r) => (
          <li key={r.forecast_time} className="border-b border-stone-line py-1">
            {new Date(r.forecast_time).toLocaleString("en-GB", { timeZone: "Europe/London" })} · {r.temp_c}°C · rain{" "}
            {r.precip_probability_pct}% · wind {r.wind_mph} mph
          </li>
        ))}
      </ul>
    </div>
  );
}