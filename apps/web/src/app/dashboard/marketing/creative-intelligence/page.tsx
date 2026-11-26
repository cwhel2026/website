"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { MarketingCard } from "@/components/marketing-director-shell";
import { withLoadError } from "@/lib/load-errors";

export default function CreativeIntelligencePage() {
  const [brief, setBrief] = useState<{ copy_for_chatgpt?: string } | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<{ copy_for_chatgpt?: string }>("/api/v1/marketing/surfacecoat/creative-brief", token)
      .then(setBrief)
      .catch(withLoadError(() => setBrief(null)));
  }, []);

  const copy = () => {
    if (brief?.copy_for_chatgpt) navigator.clipboard.writeText(brief.copy_for_chatgpt);
  };

  return (
    <MarketingCard title="Creative brief for ChatGPT">
      <p className="mb-3 text-xs text-slate-500">Built from imported organic posts — not generic templates.</p>
      <button
        type="button"
        onClick={copy}
        className="mb-3 w-full rounded-full bg-[#1a1a1a] py-2 text-sm font-semibold text-[#eab308]"
      >
        Copy creative brief
      </button>
      <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-100 p-3 text-xs">
        {brief?.copy_for_chatgpt || "Connect Meta and import posts to generate a brief."}
      </pre>
    </MarketingCard>
  );
}