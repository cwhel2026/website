import Link from "next/link";
import { StockImage } from "@/components/site/stock-image";
import { SERVICE_CARDS } from "@/lib/site-content";
import { serviceMedia } from "@/lib/media-assets";

export const metadata = {
  title: "Restoration services",
  description: "Tarmac, block paving, imprinted concrete and commercial surface restoration.",
};

export default function ServicesIndexPage() {
  return (
    <div className="site-container py-14 md:py-20">
      <p className="section-eyebrow">Services</p>
      <h1 className="mt-2 font-display text-4xl font-semibold tracking-tight text-asphalt md:text-[2.75rem]">
        Restoration without unnecessary replacement
      </h1>
      <p className="mt-4 max-w-2xl text-lg leading-relaxed text-asphalt/75">
        Active services are loaded from your catalogue — only advertise what you are ready to deliver.
      </p>
      <ServicesGrid />
    </div>
  );
}

function ServicesGrid() {
  return (
    <div className="mt-10 flex gap-4 overflow-x-auto pb-2 snap-x snap-mandatory [-ms-overflow-style:none] [scrollbar-width:none] md:grid md:grid-cols-2 md:gap-6 md:overflow-visible md:pb-0 [&::-webkit-scrollbar]:hidden">
      {SERVICE_CARDS.map((s) => {
        const media = serviceMedia(s.slug);
        return (
          <Link
            key={s.slug}
            href={s.href}
            className="group min-w-[85vw] max-w-[85vw] snap-start overflow-hidden rounded-lg border border-stone-line bg-white transition hover:shadow-lift md:min-w-0 md:max-w-none"
          >
            {media ? (
              <StockImage asset={media} aspect="aspect-[2/1]" sizes="(max-width: 768px) 85vw, 50vw" />
            ) : (
              <div
                className="flex aspect-[2/1] items-center justify-center bg-asphalt-900 px-4 text-center text-xs text-stone-wash/80"
                role="img"
                aria-label={`${s.name} — verified photography pending`}
              >
                Verified UK reference photo pending
              </div>
            )}
            <div className="p-5">
              <h2 className="font-display text-xl font-semibold group-hover:text-restore-dark">{s.name}</h2>
              <p className="mt-2 line-clamp-2 text-sm text-asphalt/70">{s.blurb}</p>
            </div>
          </Link>
        );
      })}
    </div>
  );
}