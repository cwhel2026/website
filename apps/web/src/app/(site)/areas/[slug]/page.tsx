import Link from "next/link";
import { notFound } from "next/navigation";
import { LOCAL_PAGES } from "@/lib/site-content";

export function generateStaticParams() {
  return LOCAL_PAGES.map((page) => ({ slug: page.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const page = LOCAL_PAGES.find((item) => item.slug === slug);
  if (!page) return { title: "Area" };
  return { title: page.title, description: page.intro };
}

export default async function AreaPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const page = LOCAL_PAGES.find((item) => item.slug === slug);
  if (!page) notFound();

  return (
    <article>
      <header className="bg-brand-ink text-white">
        <div className="site-container py-12 md:py-16">
          <p className="section-eyebrow text-brand-gold">Local service</p>
          <h1 className="mt-3 max-w-3xl font-display text-4xl font-medium leading-tight md:text-5xl">{page.title}</h1>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/75">{page.intro}</p>
        </div>
      </header>
      <div className="site-container py-12 md:py-16">
        <ul className="grid gap-4">
          {page.bullets.map((bullet) => (
            <li key={bullet} className="border-t border-brand-line pt-4 text-sm leading-relaxed">
              {bullet}
            </li>
          ))}
        </ul>
        <div className="mt-10 flex flex-col gap-3 sm:flex-row">
          <Link href="/quote?service=tarmac-restoration" className="btn-primary">
            Get my instant estimate
          </Link>
          <Link href="/service-areas" className="btn-secondary">
            All areas
          </Link>
        </div>
      </div>
    </article>
  );
}
