"use client";

import Link from "next/link";
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
    <header className="sticky top-0 z-40 border-b border-stone-line/80 bg-stone-wash/95 backdrop-blur-md">
      <div className="site-container flex items-center justify-between gap-4 py-4">
        <Link href="/" className="group">
          <span className="font-display text-xl font-semibold tracking-tight text-asphalt">
            Revive My Drive
          </span>
          <span className="mt-0.5 block text-[11px] uppercase tracking-[0.18em] text-asphalt/60">
            Surface restoration · North West
          </span>
        </Link>

        <nav className="hidden items-center gap-8 lg:flex" aria-label="Primary">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`text-sm font-medium transition ${
                pathname.startsWith(item.href) ? "text-restore-dark" : "text-asphalt/75 hover:text-asphalt"
              }`}
            >
              {item.label}
            </Link>
          ))}
          <Link href="/dashboard" className="text-sm font-medium text-asphalt/60 hover:text-asphalt">
            Business login
          </Link>
          <Link href="/quote" className="btn-primary px-5 py-2.5">
            Get instant quote
          </Link>
        </nav>

        <div className="flex items-center gap-2 lg:hidden">
          <Link href="/quote" className="btn-primary px-4 py-2.5 text-xs">
            Quote
          </Link>
          <button
            type="button"
            className="rounded border border-stone-line px-3 py-2 text-sm"
            aria-expanded={open}
            onClick={() => setOpen(!open)}
          >
            Menu
          </button>
        </div>
      </div>
      {open && (
        <nav className="border-t border-stone-line bg-white px-4 py-4 lg:hidden" aria-label="Mobile">
          <ul className="space-y-3">
            {nav.map((item) => (
              <li key={item.href}>
                <Link href={item.href} className="block text-base font-medium" onClick={() => setOpen(false)}>
                  {item.label}
                </Link>
              </li>
            ))}
            <li>
              <Link href="/contact" onClick={() => setOpen(false)}>
                Contact
              </Link>
            </li>
          </ul>
        </nav>
      )}
    </header>
  );
}