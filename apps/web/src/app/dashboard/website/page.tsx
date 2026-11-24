"use client";

export default function WebsiteDashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold text-asphalt">Website & marketing</h1>
      <p className="mt-2 text-sm text-asphalt/70">
        CMS, landing page builder, A/B tests and live page management — scaffold for the acquisition engine.
        Attribution events flow through existing marketing endpoints when analytics consent is granted.
      </p>
      <dl className="mt-8 grid gap-4 text-sm md:grid-cols-2">
        <Item title="Live public site" detail="Homepage, services, multi-step quote, commercial enquiry" status="Published (code deploy)" />
        <Item title="Landing page builder" detail="Dashboard editor + approval queue" status="Planned — use /c/[slug] flyers today" />
        <Item title="Media library" detail="Before/after pairs with publish permissions" status="Not started" />
        <Item title="Quotation funnel" detail="Session + attribution funnel events" status="Active (consent-gated)" />
        <Item title="A/B experiments" detail="Requires traffic volume + approval" status="Not started" />
        <Item title="SEO pages" detail="Regional guides + sitemap.xml" status="Partial" />
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