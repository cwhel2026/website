"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { EmptyState, MarketingCard } from "@/components/marketing-director-shell";
import { withLoadError } from "@/lib/load-errors";

type Post = {
  id: string;
  platform: string;
  permalink?: string;
  caption?: string;
  published_at?: string;
  analysis?: { angles?: string[] };
};

export default function SocialPostsPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const token = getToken();

  const load = () => {
    if (!token) return;
    apiGet<Post[]>("/api/v1/marketing/surfacecoat/organic-posts", token)
      .then(setPosts)
      .catch(withLoadError(() => setPosts([])));
  };

  useEffect(load, [token]);

  async function syncNow() {
    if (!token) return;
    setSyncing(true);
    setMsg(null);
    try {
      const res = await apiPost<Record<string, unknown>>(
        "/api/v1/marketing/surfacecoat/organic-posts/sync",
        {},
        token,
      );
      const fb = (res.facebook as { message?: string; imported?: number }) || {};
      const ig = (res.instagram as { message?: string; imported?: number }) || {};
      setMsg(`FB: ${fb.message || `${fb.imported ?? 0} new`} · IG: ${ig.message || `${ig.imported ?? 0} new`}`);
      load();
    } catch {
      setMsg("Sync failed — check Meta credentials in Integrations.");
    } finally {
      setSyncing(false);
    }
  }

  return (
    <>
      <MarketingCard title="Imported posts">
        <p className="mb-3 text-xs text-slate-500">
          Posts you publish manually on Facebook/Instagram are imported here. Nothing is auto-published.
        </p>
        <button
          type="button"
          disabled={syncing}
          onClick={syncNow}
          className="w-full rounded-full bg-[#eab308] py-2 text-sm font-semibold text-[#1a1a1a] disabled:opacity-60"
        >
          {syncing ? "Syncing…" : "Sync from Meta"}
        </button>
        {msg && <p className="mt-2 text-xs">{msg}</p>}
      </MarketingCard>
      {posts.length === 0 ? (
        <EmptyState message="No posts yet. Connect Meta and run sync, or wait for webhook delivery." />
      ) : (
        <ul className="space-y-3">
          {posts.map((p) => (
            <li key={p.id} className="rounded-xl border border-white/10 bg-white p-3 text-sm text-[#1a1a1a]">
              <p className="text-xs uppercase text-slate-500">{p.platform}</p>
              <p className="line-clamp-3">{p.caption || "(no caption)"}</p>
              {p.analysis?.angles?.length ? (
                <p className="mt-1 text-xs text-slate-600">Angles: {p.analysis.angles.join(", ")}</p>
              ) : null}
              {p.permalink && (
                <a href={p.permalink} target="_blank" rel="noreferrer" className="mt-2 inline-block text-xs underline">
                  View post
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
    </>
  );
}