"use client";

import Link from "next/link";

const REQUIRED_ASSETS = [
  { id: "hero-home", detail: "Homepage hero", status: "Tarmac restoration photograph — WebP/AVIF" },
  { id: "before-after-pair", detail: "Before and after pairs on the public site", status: "Seven restoration pairs" },
  { id: "per-service", detail: "One photograph per service", status: "Tarmac, block paving, imprinted concrete, repairs, commercial" },
  { id: "regional", detail: "Optional imagery for /areas pages", status: "Text-only" },
];

export default function WebsiteDashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold text-asphalt">Website &amp; marketing</h1>
        <p className="mt-2 text-sm text-asphalt/70">
        Public imagery is configured in <code className="text-xs">apps/web/src/lib/media-assets.ts</code> with
        committed files under <code className="text-xs">apps/web/public/media/approved/</code>. Captions name the
        service. They do not name a customer or a town. Pre-launch mode is on unless{" "}
        <code className="text-xs">NEXT_PUBLIC_PRELAUNCH</code> is <code className="text-xs">false</code>. Turning it
        off hides the March 2027 notice. It does not confirm bookings by itself.
      </p>

      <section className="mt-8 rounded-lg border border-stone-line bg-white p-6">
        <h2 className="font-semibold text-asphalt">Media requirements</h2>
        <ul className="mt-4 space-y-3 text-sm">
          {REQUIRED_ASSETS.map((a) => (
            <li key={a.id} className="flex flex-wrap justify-between gap-2 border-b border-stone-line pb-2">
              <span>
                <strong>{a.id}</strong> — {a.detail}
              </span>
              <span className="text-xs font-medium uppercase tracking-wide text-restore-dark">{a.status}</span>
            </li>
          ))}
        </ul>
        <p className="mt-4 text-xs text-asphalt/60">
          Upload workflow (S3 or CDN-backed storage) is not yet connected. Until then, add owned JPEG/WEBP files to{" "}
          <code className="text-xs">public/media/</code>, update <code className="text-xs">media-assets.ts</code>, and
          redeploy web. Full manifest: <code className="text-xs">public/media/manifest.json</code>.
        </p>
        <Link href="/api/version" className="mt-4 inline-block text-sm font-semibold text-restore-dark hover:underline">
          Check deployed web build version →
        </Link>
      </section>

      <dl className="mt-8 grid gap-4 text-sm md:grid-cols-2">
        <Item title="Live public site" detail="Restoration photographs, quote funnel (provisional + submit)" status="Implemented — verify on Railway" />
        <Item title="Quotation funnel" detail="No CRM records until customer submit" status="Implemented" />
        <Item title="Media library" detail="Manifest + dashboard checklist" status="Scaffolded" />
        <Item title="Landing page builder" detail="Dashboard editor + approval queue" status="Not started" />
        <Item title="A/B experiments" detail="Requires traffic volume + approval" status="Not started" />
        <Item title="SEO pages" detail="Sitemap + regional guides partial" status="Partial" />
      </dl>
    </div>
  );
}

function Item({ title, detail, status }: { title: string; detail: string; status: string }) {
  return (
    <div className="rounded-lg border border-stone-line bg-white p-4">
      <dt className="font-semibold">{title}</dt>
      <dd className="mt-1 text-asphalt/70">{detail}</dd>
      <dd className="mt-2 text-xs font-medium uppercase tracking-wide text-restore-dark">{status}</dd>
    </div>
  );
}