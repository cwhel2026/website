"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function StickyQuote() {
  const path = usePathname();
  if (path.startsWith("/dashboard") || path.startsWith("/quote")) return null;
  return (
    <div className="fixed inset-x-0 bottom-0 z-30 border-t border-stone-line bg-white/95 p-3 backdrop-blur md:hidden">
      <Link href="/quote" className="btn-primary flex w-full justify-center">
        Get instant quote
      </Link>
    </div>
  );
}