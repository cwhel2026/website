"use client";

import Link from "next/link";
import { publicBrand } from "@/lib/public-brand";
import { usePathname } from "next/navigation";
import { useState } from "react";

const nav = [
  { href: "/services", label: "Services" },
  { href: "/commercial", label: "Commercial" },
  { href: "/service-areas", label: "Areas" },
  { href: "/gallery", label: "Gallery" },
  { href: "/faq", label: "FAQ" },
];

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-stone-line/90 bg-stone-wash/97 shadow-[0_1px_0_rgba(26,31,30,0.04)] backdrop-blur-md">
      <div className="h-1 bg-gradient-to-r from-restore-green via-restore-dark to-asphalt" aria-hidden />
      <div className="site-container flex items-center justify-between gap-4 py-3.5 md:py-4">
        <Link href="/" className="group flex items-center gap-3">
          <span
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-asphalt font-display text-lg font-semibold text-white shadow-sm"
            aria-hidden
          >
            S
          </span>
          <span>
            <span className="block font-display text-lg font-semibold tracking-tight text-asphalt md:text-xl">
              {publicBrand.tradingName}
            </span>
            <span className="mt-0.5 block text-[10px] font-semibold uppercase tracking-[0.22em] text-asphalt/55">
              {publicBrand.legalName}
            </span>
          </span>
        </Link>

        <nav className="hidden items-center gap-7 xl:flex" aria-label="Primary">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`text-sm font-medium tracking-tight transition ${
                pathname.startsWith(item.href) ? "text-restore-dark" : "text-asphalt/72 hover:text-asphalt"
              }`}
            >
              {item.label}
            </Link>
          ))}
          <Link href="/dashboard" className="text-sm font-medium text-asphalt/55 hover:text-asphalt">
            Business login
          </Link>
          <Link href="/quote" className="btn-primary px-5 py-2.5 text-sm">
            Get instant quote
          </Link>
        </nav>

        <div className="flex items-center gap-2 xl:hidden">
          <Link href="/quote" className="btn-primary px-3.5 py-2 text-xs">
            Quote
          </Link>
          <button
            type="button"
            className="rounded-md border border-stone-line bg-white px-3 py-2 text-sm font-medium text-asphalt"
            aria-expanded={open}
            onClick={() => setOpen(!open)}
          >
            Menu
          </button>
        </div>
      </div>
      {open ? (
        <nav className="border-t border-stone-line bg-white px-4 py-4 xl:hidden" aria-label="Mobile">
          <ul className="space-y-3">
            {nav.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="block text-base font-medium text-asphalt"
                  onClick={() => setOpen(false)}
                >
                  {item.label}
                </Link>
              </li>
            ))}
            <li>
              <Link href="/contact" className="block text-base font-medium" onClick={() => setOpen(false)}>
                Contact
              </Link>
            </li>
          </ul>
        </nav>
      ) : null}
    </header>
  );
}