"use client";

import Link from "next/link";
import { publicBrand } from "@/lib/public-brand";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const nav = [
  { href: "/", label: "Home", match: "exact" as const },
  { href: "/services", label: "Our services", match: "prefix" as const },
  { href: "/transformations", label: "Transformations", match: "prefix" as const },
  { href: "/how-it-works", label: "How it works", match: "prefix" as const },
  { href: "/service-areas", label: "Areas we cover", match: "prefix" as const },
  { href: "/contact", label: "Contact", match: "prefix" as const },
];

function isCurrent(pathname: string, href: string, match: "exact" | "prefix") {
  if (match === "exact") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-brand-ink pt-[env(safe-area-inset-top)] text-white">
      <div className="site-container flex items-center justify-between gap-4 py-3">
        <Link href="/" className="min-w-0">
          <span className="block font-display text-xl font-medium tracking-tight text-white">
            {publicBrand.tradingName}
          </span>
          <span className="mt-0.5 block text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-gold">
            {publicBrand.tagline}
          </span>
        </Link>

        <nav className="hidden items-center gap-6 xl:flex" aria-label="Primary">
          {nav.map((item) => {
            const current = isCurrent(pathname, item.href, item.match);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={current ? "page" : undefined}
                className={`text-sm font-medium ${current ? "text-brand-gold" : "text-white/80 hover:text-white"}`}
              >
                {item.label}
              </Link>
            );
          })}
          <Link href="/quote" className="btn-primary px-4 py-2.5 text-sm">
            Get an instant estimate
          </Link>
        </nav>

        <button
          type="button"
          className="inline-flex min-h-11 min-w-11 items-center justify-center border border-white/25 px-3 text-sm font-semibold xl:hidden"
          aria-expanded={open}
          aria-controls="mobile-nav"
          onClick={() => setOpen((value) => !value)}
        >
          {open ? "Close" : "Menu"}
        </button>
      </div>
      {open ? (
        <nav id="mobile-nav" className="border-t border-white/10 bg-brand-ink px-4 py-2 xl:hidden" aria-label="Mobile">
          <ul>
            {nav.map((item) => (
              <li key={item.href} className="border-b border-white/10">
                <Link
                  href={item.href}
                  className="flex min-h-12 items-center text-base font-medium text-white"
                  onClick={() => setOpen(false)}
                >
                  {item.label}
                </Link>
              </li>
            ))}
            <li className="py-3">
              <Link href="/quote" className="btn-primary w-full" onClick={() => setOpen(false)}>
                Get an instant estimate
              </Link>
            </li>
          </ul>
        </nav>
      ) : null}
    </header>
  );
}
