"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect } from "react";
import { apiPost } from "@/lib/api";

export default function CampaignLandingPage() {
  const params = useParams();
  const slug = params.slug as string;

  useEffect(() => {
    if (!slug) return;
    apiPost("/api/v1/marketing/attribution/track", {
      source: `flyer_${slug}`,
      medium: "qr",
      content: slug,
    }).catch(() => {});
  }, [slug]);

  return (
    <div className="mx-auto max-w-xl px-4 py-16 text-center">
      <h1 className="text-2xl font-semibold text-emerald-950">SurfaceCoat</h1>
      <p className="mt-4 text-emerald-900/80">
        You scanned a regional flyer (campaign ref: {slug}). Get a provisional quote for your driveway or car park
        restoration.
      </p>
      <Link
        href={`/quote?campaign=flyer_${slug}`}
        className="mt-8 inline-block rounded-full bg-emerald-900 px-6 py-3 font-semibold text-white"
      >
        Get instant quote
      </Link>
    </div>
  );
}