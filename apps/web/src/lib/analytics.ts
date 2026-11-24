"use client";

import { apiPost } from "@/lib/api";

const SESSION_KEY = "rmd_session";
const UTM_KEY = "rmd_utm";

export type UtmParams = {
  source?: string;
  medium?: string;
  campaign?: string;
  content?: string;
};

export function getSessionId(): string {
  if (typeof window === "undefined") return "ssr";
  let id = sessionStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

export function captureUtmFromUrl(): UtmParams {
  if (typeof window === "undefined") return {};
  const params = new URLSearchParams(window.location.search);
  const utm: UtmParams = {
    source: params.get("utm_source") ?? params.get("campaign") ?? undefined,
    medium: params.get("utm_medium") ?? undefined,
    campaign: params.get("utm_campaign") ?? undefined,
    content: params.get("utm_content") ?? undefined,
  };
  if (Object.values(utm).some(Boolean)) {
    sessionStorage.setItem(UTM_KEY, JSON.stringify(utm));
  }
  return getStoredUtm();
}

export function getStoredUtm(): UtmParams {
  if (typeof window === "undefined") return {};
  try {
    const raw = sessionStorage.getItem(UTM_KEY);
    return raw ? (JSON.parse(raw) as UtmParams) : {};
  } catch {
    return {};
  }
}

export async function trackFunnel(event: string, step?: number): Promise<void> {
  const consent = localStorage.getItem("rmd_analytics_consent");
  if (consent !== "granted") return;
  const utm = getStoredUtm();
  try {
    await apiPost("/api/v1/marketing/attribution/track", {
      source: utm.source ?? "website",
      medium: utm.medium ?? "organic",
      content: step !== undefined ? `funnel:${event}:step${step}` : `funnel:${event}`,
    });
  } catch {
    /* non-blocking */
  }
}