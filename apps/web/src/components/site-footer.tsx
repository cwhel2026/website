import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-emerald-900/10 bg-emerald-950 text-emerald-50">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-12 md:grid-cols-3">
        <div>
          <p className="text-lg font-semibold">Revive My Drive</p>
          <p className="mt-2 text-sm text-emerald-100/80">
            Specialist driveway and hard surface restoration serving Lancashire,
            Merseyside, Greater Manchester and the wider North West.
          </p>
          <p className="mt-4 text-sm text-emerald-100/70">Headquarters: Burscough, Lancashire</p>
        </div>
        <div className="text-sm">
          <p className="font-semibold">Quick links</p>
          <ul className="mt-3 space-y-2 text-emerald-100/80">
            <li>
              <Link href="/quote" className="hover:text-white">
                Instant quotation
              </Link>
            </li>
            <li>
              <Link href="/privacy" className="hover:text-white">
                Privacy policy
              </Link>
            </li>
            <li>
              <Link href="/terms" className="hover:text-white">
                Terms and conditions
              </Link>
            </li>
          </ul>
        </div>
        <div className="text-sm">
          <p className="font-semibold">Provisional quotations</p>
          <p className="mt-3 text-emerald-100/80">
            Online prices are indicative and subject to on-site measurement, surface
            condition verification and safe access.
          </p>
        </div>
      </div>
      <div className="border-t border-emerald-800/50 px-4 py-4 text-center text-xs text-emerald-200/60">
        © {new Date().getFullYear()} Revive My Drive. All rights reserved.
      </div>
    </footer>
  );
}