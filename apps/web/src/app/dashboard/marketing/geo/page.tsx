"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { MarketingCard } from "@/components/marketing-director-shell";
import { withLoadError } from "@/lib/load-errors";

export default function GeoPage() {
  const [geo, setGeo] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<{ programme: { geo?: Record<string, unknown> }; geo?: Record<string, unknown> }>(
      "/api/v1/marketing/surfacecoat/launch-programme",
      token,
    )
      .then((r) => setGeo(r.geo || r.programme?.geo || null))
      .catch(withLoadError(() => setGeo(null)));
  }, []);

  return (
    <MarketingCard title="Geographical focus">
      <p className="text-sm">
        Base: Preston · default radius {String((geo as { radius_miles?: number })?.radius_miles ?? 20)} miles
      </p>
      <p className="mt-2 text-xs text-slate-500">
        Recommendations consider diary capacity and weather — see regional marketing hub for territory detail.
      </p>
    </MarketingCard>
  );
}