import Link from "next/link";
import { FAQ_ITEMS } from "@/lib/site-content";

export const metadata = {
  title: "Questions",
  description: "Cost, timing, repairs, access, weather, return to use, and which surfaces can be restored.",
};

export default function FaqPage() {
  const schema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: FAQ_ITEMS.map((item) => ({
      "@type": "Question",
      name: item.q,
      acceptedAnswer: { "@type": "Answer", text: item.a },
    })),
  };

  return (
    <div>
      <header className="bg-brand-ink text-white">
        <div className="site-container py-12 md:py-16">
          <p className="section-eyebrow text-brand-gold">Questions</p>
          <h1 className="mt-3 font-display text-4xl font-medium md:text-5xl">Clear answers.</h1>
        </div>
      </header>
      <div className="site-container py-12 md:py-16">
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
        <dl className="divide-y divide-brand-line border-y border-brand-line">
          {FAQ_ITEMS.map((item) => (
            <div key={item.q} className="py-6">
              <dt className="font-display text-2xl font-medium">{item.q}</dt>
              <dd className="mt-3 max-w-3xl text-sm leading-relaxed text-brand-ink/75">{item.a}</dd>
            </div>
          ))}
        </dl>
        <Link href="/quote" className="btn-primary mt-10">
          Get my instant estimate
        </Link>
      </div>
    </div>
  );
}
