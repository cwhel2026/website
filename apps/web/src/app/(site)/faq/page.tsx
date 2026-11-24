import Link from "next/link";
import { FAQ_ITEMS } from "@/lib/site-content";

export const metadata = { title: "Frequently asked questions" };

export default function FaqPage() {
  return (
    <div className="site-container py-16 md:py-24">
      <p className="section-eyebrow">FAQ</p>
      <h1 className="mt-2 font-display text-4xl font-semibold text-asphalt">Questions answered honestly</h1>
      <dl className="mt-10 space-y-8">
        {FAQ_ITEMS.map((item) => (
          <div key={item.q}>
            <dt className="font-display text-lg font-semibold text-asphalt">{item.q}</dt>
            <dd className="mt-2 text-asphalt/75">{item.a}</dd>
          </div>
        ))}
      </dl>
      <Link href="/quote" className="btn-primary mt-12 inline-flex">
        Start instant quote
      </Link>
    </div>
  );
}