"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function StickyQuote() {
  const path = usePathname();
  if (path.startsWith("/dashboard") || path.startsWith("/quote")) return null;
  return (
    <div
      className="fixed inset-x-0 z-30 border-t border-brand-line bg-brand-paper/95 px-4 pt-3 backdrop-blur md:hidden"
      style={{
        bottom: "var(--consent-offset, 0px)",
        paddingBottom: "calc(0.75rem + env(safe-area-inset-bottom))",
      }}
    >
      <Link href="/quote" className="btn-primary w-full">
        Get an instant estimate
      </Link>
    </div>
  );
}
