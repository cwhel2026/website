import Link from "next/link";
import type { ReactNode } from "react";
import { StockImage } from "@/components/site/stock-image";
import { HOW_IT_WORKS, type ServiceEstimate } from "@/lib/site-content";
import { serviceMedia } from "@/lib/media-assets";

export function ServicePage({
  title,
  intro,
  benefits,
  slug,
  estimate = "on-request",
}: {
  title: string;
  intro: string;
  benefits: string[];
  slug: string;
  estimate?: ServiceEstimate;
}) {
  const media = serviceMedia(slug);
  return (
    <article>
      <header className="bg-brand-ink text-white">
        <div className="site-container py-12 md:py-16">
          <p className="section-eyebrow text-brand-gold">Our services</p>
          <h1 className="mt-3 max-w-3xl font-display text-4xl font-medium leading-[1.05] md:text-5xl">{title}</h1>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/75">{intro}</p>
        </div>
      </header>

      <div className="site-container py-12 md:py-16">
        {media ? (
          <figure>
            <StockImage asset={media} aspect="aspect-[21/9]" sizes="(max-width: 1152px) 100vw, 1152px" />
            <figcaption className="mt-2 text-xs leading-relaxed text-brand-ink/60">
              {media.caption ?? media.alt}
            </figcaption>
          </figure>
        ) : (
          <p
            className="border border-brand-line bg-white px-4 py-8 text-sm text-brand-ink/70"
            role="status"
          >
            A verified photograph for this service has not been approved yet. We are not using a stand-in image.
          </p>
        )}

        <h2 className="mt-12 font-display text-3xl font-medium">What this covers</h2>
        <ul className="mt-6 grid gap-4 md:grid-cols-3">
          {benefits.map((benefit) => (
            <li key={benefit} className="border-t-2 border-brand-gold pt-4 text-sm leading-relaxed text-brand-ink/80">
              {benefit}
            </li>
          ))}
        </ul>

        <h2 className="mt-14 font-display text-3xl font-medium">How the work is arranged</h2>
        <ol className="mt-6 grid gap-6 md:grid-cols-2">
          {HOW_IT_WORKS.map((step, index) => (
            <li key={step.title} className="border-t border-brand-line pt-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand-ink">0{index + 1}</p>
              <p className="mt-2 font-semibold">{step.title}</p>
              <p className="mt-1 text-sm leading-relaxed text-brand-ink/70">{step.detail}</p>
            </li>
          ))}
        </ol>
        <p className="mt-6 max-w-2xl text-sm leading-relaxed text-brand-ink/70">
          Coating appointments depend on suitable weather and surface conditions.
        </p>

        <div className="mt-10 flex flex-col gap-3 sm:flex-row">
          <Link href={`/quote?service=${slug}`} className="btn-primary">
            {estimate === "instant" ? "Get my instant estimate" : "Request a quotation"}
          </Link>
          <Link href="/service-areas" className="btn-secondary">
            Areas we cover
          </Link>
        </div>
        {estimate === "instant" ? (
          <p className="mt-4 max-w-2xl text-sm leading-relaxed text-brand-ink/70">
            You will see one total. It is not a confirmed booking.
          </p>
        ) : (
          <p className="mt-4 max-w-2xl text-sm leading-relaxed text-brand-ink/70">
            A published instant price is available for tarmac restoration. This service does not show a price until
            one is confirmed, and requesting a quotation does not confirm a booking.
          </p>
        )}
      </div>
    </article>
  );
}

export function ServiceFaq({ children }: { children: ReactNode }) {
  return <section className="site-container border-t border-brand-line py-12">{children}</section>;
}
