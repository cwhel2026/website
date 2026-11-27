import Link from "next/link";
import { publicBrand } from "@/lib/public-brand";
import { SERVICE_CARDS } from "@/lib/site-content";

const explore = [
  { href: "/services", label: "Our services" },
  { href: "/transformations", label: "Transformations" },
  { href: "/how-it-works", label: "How it works" },
  { href: "/service-areas", label: "Areas we cover" },
  { href: "/faq", label: "Questions" },
  { href: "/contact", label: "Contact" },
  { href: "/commercial", label: "Commercial enquiry" },
];

export function SiteFooter() {
  const year = new Date().getFullYear();
  return (
    <footer className="bg-brand-ink text-white">
      <div className="site-container grid gap-10 py-14 md:grid-cols-4">
        <div className="md:col-span-1">
          <p className="font-display text-2xl font-medium">{publicBrand.tradingName}</p>
          <p className="mt-2 text-xs font-semibold uppercase tracking-[0.18em] text-brand-gold">
            {publicBrand.tagline}
          </p>
          <p className="mt-4 max-w-xs text-sm leading-relaxed text-white/70">
            Driveway and surface restoration across {publicBrand.coverageAreas}.
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/75">Explore</p>
          <ul className="mt-4 space-y-2 text-sm">
            {explore.map((item) => (
              <li key={item.href}>
                <Link href={item.href} className="text-white/80 hover:text-white">
                  {item.label}
                </Link>
              </li>
            ))}
            <li>
              <Link href="/dashboard" className="text-white/75 hover:text-white">
                Business login
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/75">Services</p>
          <ul className="mt-4 space-y-2 text-sm">
            {SERVICE_CARDS.map((service) => (
              <li key={service.slug}>
                <Link href={service.href} className="text-white/80 hover:text-white">
                  {service.name}
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/75">Estimate</p>
          <p className="mt-4 text-sm leading-relaxed text-white/70">
            The online estimate is free. A booking request is recorded for the team and is not a confirmed appointment.
          </p>
          <Link href="/quote" className="btn-primary mt-5">
            Get an instant estimate
          </Link>
          <ul className="mt-6 space-y-2 text-sm">
            <li>
              <Link href="/privacy" className="text-white/70 hover:text-white">
                Privacy
              </Link>
            </li>
            <li>
              <Link href="/terms" className="text-white/70 hover:text-white">
                Terms
              </Link>
            </li>
          </ul>
        </div>
      </div>
      <div className="border-t border-white/10">
        <p className="site-container py-5 text-xs leading-relaxed text-white/75">
          © {year} {publicBrand.legalName}. Photographs marked as reference or illustrative are not completed
          SurfaceCoat projects. We do not publish reviews, accreditations or project history we cannot verify.
        </p>
      </div>
    </footer>
  );
}
