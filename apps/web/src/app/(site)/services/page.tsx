import Link from "next/link";
import { StockImage } from "@/components/site/stock-image";
import { SERVICE_CARDS } from "@/lib/site-content";
import { serviceMedia } from "@/lib/media-assets";

export const metadata = {
  title: "Our services",
  description:
    "Tarmac restoration, block paving, pattern-imprinted concrete, surface repairs, commercial restoration and car park line marking.",
};

export default function ServicesIndexPage() {
  return (
    <div>
      <header className="bg-brand-ink text-white">
        <div className="site-container py-12 md:py-16">
          <p className="section-eyebrow text-brand-gold">Our services</p>
          <h1 className="mt-3 max-w-3xl font-display text-4xl font-medium leading-tight md:text-5xl">
            Restore the surface. Leave the base where it is sound.
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/75">
            Each service has its own page. An instant price is published for tarmac restoration. Other services are
            quoted when a price is confirmed. None of these pages confirm a booking.
          </p>
        </div>
      </header>
      <div className="site-container grid gap-10 py-12 md:py-16">
        {SERVICE_CARDS.map((service) => {
          const media = serviceMedia(service.slug);
          return (
            <article key={service.slug} className="grid gap-6 border-t border-brand-line pt-8 md:grid-cols-[1.1fr_0.9fr] md:items-center">
              <div>
                <h2 className="font-display text-3xl font-medium">{service.name}</h2>
                <p className="mt-3 max-w-xl text-sm leading-relaxed text-brand-ink/75">{service.blurb}</p>
                <p className="mt-3 text-sm font-medium">
                  {service.estimate === "instant" ? "Instant estimate available." : "Price confirmed before it is shown."}
                </p>
                <Link href={service.href} className="mt-4 inline-flex min-h-11 items-center text-sm font-semibold">
                  View service
                </Link>
              </div>
              {media ? (
                <StockImage asset={media} aspect="aspect-[16/10]" sizes="(max-width: 768px) 100vw, 40vw" />
              ) : (
                <p className="flex aspect-[16/10] items-end bg-brand-ink p-4 text-xs uppercase tracking-[0.14em] text-white/70">
                  Photograph pending approval
                </p>
              )}
            </article>
          );
        })}
      </div>
    </div>
  );
}
