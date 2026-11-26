"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { withLoadError } from "@/lib/load-errors";

type Item = { id: string; platform: string; title: string; status: string };

export default function ContentStudioPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [brief, setBrief] = useState("Seasonal driveway restoration tip for Lancashire homeowners");
  const [preview, setPreview] = useState<string | null>(null);

  const reload = () => {
    const token = getToken();
    if (!token) return;
    apiGet<Item[]>("/api/v1/marketing/content/items", token).then(setItems).catch(withLoadError(() => setItems([])));
  };

  useEffect(() => {
    reload();
  }, []);

  const generate = async () => {
    const token = getToken();
    if (!token) return;
    const res = await apiPost<{ body_preview: string }>(
      "/api/v1/marketing/content/generate",
      { platform: "facebook", brief },
      token,
    );
    setPreview(res.body_preview);
    reload();
  };

  return (
    <div className="max-w-2xl space-y-4 pb-16">
      <h1 className="text-2xl font-semibold">Content studio</h1>
      <textarea
        className="w-full rounded border p-2 text-sm"
        rows={3}
        value={brief}
        onChange={(e) => setBrief(e.target.value)}
      />
      <button type="button" onClick={generate} className="rounded bg-emerald-700 px-4 py-2 text-white">
        Generate Facebook draft
      </button>
      {preview && (
        <section className="rounded border bg-slate-50 p-3 text-sm whitespace-pre-wrap">{preview}</section>
      )}
      <ul className="text-sm">
        {items.map((i) => (
          <li key={i.id} className="border-b py-2">
            {i.platform} · {i.title} · {i.status}
          </li>
        ))}
      </ul>
    </div>
  );
}