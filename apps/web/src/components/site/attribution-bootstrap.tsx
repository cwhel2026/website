"use client";

import { useEffect } from "react";
import { captureUtmFromUrl, trackFunnel } from "@/lib/analytics";

export function AttributionBootstrap() {
  useEffect(() => {
    captureUtmFromUrl();
    void trackFunnel("page_view");
  }, []);
  return null;
}