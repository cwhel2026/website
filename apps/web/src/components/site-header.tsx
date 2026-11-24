import Link from "next/link";

const nav = [
  { href: "/services", label: "Services" },
  { href: "/quote", label: "Instant quote" },
  { href: "/service-areas", label: "Service areas" },
  { href: "/gallery", label: "Gallery" },
  { href: "/faq", label: "FAQ" },
  { href: "/contact", label: "Contact" },
];

export function SiteHeader() {
  return (
    <header className="border-b border-emerald-900/10 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4">
        <Link href="/" className="group">
          <span className="block text-lg font-semibold tracking-tight text-emerald-950">
            Revive My Drive
          </span>
          <span className="text-xs text-emerald-800/70">
            Exterior surface restoration · North West England
          </span>
        </Link>
        <nav className="hidden items-center gap-5 text-sm font-medium text-emerald-950/80 md:flex">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="hover:text-emerald-900"
            >
              {item.label}
            </Link>
          ))}
          <Link
            href="/dashboard"
            className="rounded-full bg-emerald-900 px-4 py-2 text-white hover:bg-emerald-800"
          >
            Business login
          </Link>
        </nav>
        <Link
          href="/quote"
          className="rounded-full bg-emerald-900 px-4 py-2 text-sm font-medium text-white md:hidden"
        >
          Get quote
        </Link>
      </div>
    </header>
  );
}