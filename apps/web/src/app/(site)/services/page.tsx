import Link from "next/link";
import { SERVICE_CARDS } from "@/lib/site-content";

export const metadata = {
  title: "Restoration services",
  description: "Tarmac, block paving, imprinted concrete and commercial surface restoration.",
};

export default function ServicesIndexPage() {
  return (
    <div className="site-container py-16 md:py-24">
      <p className="section-eyebrow">Services</p>
      <h1 className="mt-2 font-display text-4xl font-semibold text-asphalt">Restoration without unnecessary replacement</h1>
      <p className="mt-4 max-w-2xl text-asphalt/75">
        Active services are loaded from your catalogue — only advertise what you are ready to deliver.
      </p>
      <ServicesGrid />
    </div>
  );
}

function ServicesGrid() {
  return (
    <div className="mt-12 grid gap-6 md:grid-cols-2">
      {SERVICE_CARDS.map((s) => (
        <Link
          key={s.slug}
          href={s.href}
          className="group overflow-hidden rounded-lg border border-stone-line bg-white transition hover:shadow-lift"
        >
          <div className="aspect-[3/1] bg-gradient-to-r from-asphalt-900 to-asphalt-800" />
          <div className="p-6">
            <h2 className="font-display text-xl font-semibold group-hover:text-restore-dark">{s.name}</h2>
            <p className="mt-2 text-sm text-asphalt/70">{s.blurb}</p>
          </div>
        </Link>
      ))}
    </div>
  );
}