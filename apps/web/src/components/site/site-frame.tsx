"use client";

import { usePathname } from "next/navigation";

export function SiteFrame({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const quote = path.startsWith("/quote");
  const pad = quote
    ? "pb-[calc(var(--consent-offset,0px)+env(safe-area-inset-bottom))]"
    : "pb-[calc(4.75rem+var(--consent-offset,0px)+env(safe-area-inset-bottom))] md:pb-[var(--consent-offset,0px)]";

  return <div className={`min-h-screen overflow-x-clip bg-brand-paper text-brand-ink ${pad}`}>{children}</div>;
}
