import Link from "next/link";

export function SiteFooter() {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-asphalt-900/10 bg-asphalt text-stone-wash">
      <div className="site-container grid gap-10 py-14 md:grid-cols-3">
        <div>
          <p className="font-display text-lg font-semibold">Revive My Drive</p>
          <p className="mt-3 max-w-xs text-sm leading-relaxed text-stone-wash/75">
            Professional exterior surface restoration for homeowners and businesses across Lancashire,
            Merseyside and Greater Manchester. Headquarters in Burscough.
          </p>
        </div>
        <FooterExplore />
        <FooterLegal />
      </div>
      <p className="border-t border-white/10 py-6 text-center text-xs text-stone-wash/50">
        © {year} Revive My Drive. All rights reserved.
      </p>
    </footer>
  );
}

function FooterExplore() {
  const links = [
    { href: "/quote", label: "Instant quote" },
    { href: "/services", label: "Services" },
    { href: "/commercial", label: "Commercial" },
    { href: "/service-areas", label: "Service areas" },
  ];
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-widest text-stone-wash/50">Explore</p>
      <ul className="mt-4 space-y-2 text-sm">
        {links.map((l) => (
          <li key={l.href}>
            <Link href={l.href} className="text-stone-wash/85 hover:text-white">
              {l.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function FooterLegal() {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-widest text-stone-wash/50">Legal</p>
      <ul className="mt-4 space-y-2 text-sm">
        <li>
          <Link href="/privacy" className="text-stone-wash/85 hover:text-white">
            Privacy
          </Link>
        </li>
        <li>
          <Link href="/terms" className="text-stone-wash/85 hover:text-white">
            Terms
          </Link>
        </li>
      </ul>
      <p className="mt-6 text-xs leading-relaxed text-stone-wash/55">
        Online quotations are provisional until site verification. We do not publish fabricated reviews
        or project photographs.
      </p>
    </div>
  );
}