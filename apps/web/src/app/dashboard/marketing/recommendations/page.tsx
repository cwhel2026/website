"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { EmptyState, MarketingCard } from "@/components/marketing-director-shell";
import { withLoadError } from "@/lib/load-errors";

type Rec = { post_id: string; platform: string; recommendation: string; confidence: string };

export default function RecommendationsPage() {
  const [items, setItems] = useState<Rec[]>([]);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<{ items: Rec[] }>("/api/v1/marketing/surfacecoat/recommendations/organic-boost", token)
      .then((r) => setItems(r.items || []))
      .catch(withLoadError(() => setItems([])));
  }, []);

  return (
    <>
      <MarketingCard title="AI recommendations">
        <p className="text-xs text-slate-500">Approval required. Default mode: recommend only.</p>
      </MarketingCard>
      {items.length === 0 ? (
        <EmptyState message="Import organic posts to receive boost recommendations." />
      ) : (
        <ul className="space-y-3">
          {items.map((r) => (
            <li key={r.post_id} className="rounded-xl bg-white p-3 text-sm text-[#1a1a1a]">
              <p className="text-xs text-slate-500">{r.platform} · {r.confidence} confidence</p>
              <p>{r.recommendation}</p>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}