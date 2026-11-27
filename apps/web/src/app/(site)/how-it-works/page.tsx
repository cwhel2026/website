import Link from "next/link";
import { RestorationVideo } from "@/components/site/restoration-video";
import { HOW_IT_WORKS } from "@/lib/site-content";

export const metadata = {
  title: "How it works",
  description:
    "Instant estimate, booking request, preparation, then a coating visit when the weather and surface are suitable.",
};

export default function HowItWorksPage() {
  return (
    <div>
      <header className="bg-brand-ink text-white">
        <div className="site-container py-12 md:py-16">
          <p className="section-eyebrow text-brand-gold">How it works</p>
          <h1 className="mt-3 max-w-3xl font-display text-4xl font-medium leading-tight md:text-5xl">
            Estimate, request, prepare, coat.
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/75">
            Coating appointments depend on suitable weather and surface conditions.
          </p>
        </div>
      </header>
      <div className="site-container py-12 md:py-16">
        <ol className="grid gap-8">
          {HOW_IT_WORKS.map((step, index) => (
            <li key={step.title} className="grid gap-3 border-t border-brand-line pt-6 md:grid-cols-[6rem_1fr]">
              <p className="font-display text-3xl text-brand-ink">0{index + 1}</p>
              <div>
                <h2 className="font-display text-2xl font-medium">{step.title}</h2>
                <p className="mt-2 max-w-2xl text-sm leading-relaxed text-brand-ink/75">{step.detail}</p>
              </div>
            </li>
          ))}
        </ol>
        <RestorationVideo title="Restoration film" />
        <p className="mt-10 max-w-2xl text-sm leading-relaxed text-brand-ink/70">
          A short film of our own work will be added here when we have footage. It will not play on its own, and it
          will not be a stand-in clip.
        </p>
        <Link href="/quote" className="btn-primary mt-8">
          Get my instant estimate
        </Link>
      </div>
    </div>
  );
}
