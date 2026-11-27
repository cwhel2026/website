"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect } from "react";
import { getStoredUtm, trackFunnel } from "@/lib/analytics";

const UTM_KEY = "rmd_utm";

export default function CampaignLandingPage() {
  const params = useParams();
  const slug = params.slug as string;

  useEffect(() => {
    if (!slug || typeof window === "undefined") return;
    const existing = getStoredUtm();
    if (!existing.source && !existing.campaign) {
      sessionStorage.setItem(
        UTM_KEY,
        JSON.stringify({ source: `flyer_${slug}`, medium: "qr", campaign: slug, content: slug }),
      );
    }
    void trackFunnel("flyer_landing");
  }, [slug]);

  return (
    <div className="site-container max-w-xl py-16">
      <p className="section-eyebrow">SurfaceCoat</p>
      <h1 className="mt-3 font-display text-4xl font-medium">Your estimate starts here.</h1>
      <p className="mt-4 text-sm leading-relaxed text-brand-ink/75">
        This page keeps the campaign reference {slug} with your estimate. Analytics are sent only after you allow them.
      </p>
      <Link href={`/quote?campaign=flyer_${slug}`} className="btn-primary mt-8">
        Get my instant estimate
      </Link>
    </div>
  );
}
