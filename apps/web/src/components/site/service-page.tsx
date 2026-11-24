import Link from "next/link";
import type { ReactNode } from "react";
import { StockImage } from "@/components/site/stock-image";
import { serviceMedia } from "@/lib/media-assets";

export function ServicePage({
  title,
  intro,
  benefits,
  slug,
}: {
  title: string;
  intro: string;
  benefits: string[];
  slug: string;
}) {
  const media = serviceMedia(slug);
  return (
    <article className="site-container py-16 md:py-24">
      <p className="section-eyebrow">Service</p>
      <h1 className="mt-2 font-display text-4xl font-semibold text-asphalt">{title}</h1>
      <p className="mt-4 max-w-2xl text-lg text-asphalt/75">{intro}</p>

      {media ? (
        <div className="mt-10 overflow-hidden rounded-lg border border-stone-line shadow-sm">
          <StockImage asset={media} aspect="aspect-[21/9]" sizes="100vw" />
          <p className="border-t border-stone-line bg-stone-wash px-4 py-2 text-xs text-asphalt/60">
            {media.caption ??
              (media.kind === "owned_project"
                ? "Completed Revive My Drive project imagery."
                : `Licensed reference photo (${media.credit}) — not a completed Revive My Drive project.`)}
          </p>
        </div>
      ) : (
        <div
          className="mt-10 flex aspect-[21/9] items-center justify-center rounded-lg border border-dashed border-stone-line bg-stone-wash text-sm text-asphalt/55"
          role="status"
        >
          Service photography pending — upload via Website &amp; marketing when ready.
        </div>
      )}

      <h2 className="mt-12 font-display text-2xl font-semibold text-asphalt">Why customers choose this</h2>
      <ul className="mt-4 space-y-3">
        {benefits.map((b) => (
          <li key={b} className="border-l-2 border-restore-green pl-4 text-asphalt/80">
            {b}
          </li>
        ))}
      </ul>

      <h2 className="mt-12 font-display text-2xl font-semibold text-asphalt">Typical process</h2>
      <ProcessSteps />

      <div className="mt-12 flex flex-wrap gap-3">
        <Link href={`/quote?service=${slug}`} className="btn-primary">
          Instant quotation
        </Link>
        <Link href="/service-areas" className="btn-secondary">
          Check coverage
        </Link>
      </div>
    </article>
  );
}

function ProcessSteps() {
  const steps = [
    "Site suitability and measurement (online or visit).",
    "Preparation — professional washing where included.",
    "Restoration coating or sealing as specified.",
    "Aftercare guidance for your surface type.",
  ];
  return (
    <ol className="mt-4 grid gap-4 md:grid-cols-2">
      {steps.map((s, i) => (
        <li key={s} className="text-sm text-asphalt/80">
          <span className="font-bold text-restore-dark">{i + 1}.</span> {s}
        </li>
      ))}
    </ol>
  );
}

export function ServiceFaq({ children }: { children: ReactNode }) {
  return <section className="mt-16 border-t border-stone-line pt-12">{children}</section>;
}