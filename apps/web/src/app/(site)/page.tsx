import Link from "next/link";
import { BeforeAfterSlider } from "@/components/site/before-after-slider";
import { HeroPostcode } from "@/components/home/hero-postcode";
import { CoverageChecker } from "@/components/home/coverage-checker";
import { StockImage } from "@/components/site/stock-image";
import { FAQ_ITEMS, SERVICE_CARDS } from "@/lib/site-content";
import { MEDIA, serviceMedia } from "@/lib/media-assets";

export default function HomePage() {
  return (
    <>
      <section className="relative overflow-hidden bg-asphalt text-stone-wash">
        <div className="absolute inset-0">
          <StockImage
            asset={MEDIA.hero}
            priority
            aspect=""
            className="absolute inset-0 opacity-35"
            sizes="100vw"
          />
        </div>
        <div className="absolute inset-0 bg-gradient-to-r from-asphalt via-asphalt/92 to-asphalt/70" />
        <div className="site-container relative grid gap-12 py-16 md:grid-cols-2 md:items-center md:py-24 lg:py-28">
          <div className="animate-fade-up">
            <p className="section-eyebrow text-restore-green">North West surface specialists</p>
            <h1 className="mt-4 font-display text-4xl font-semibold leading-[1.08] md:text-5xl lg:text-[3.25rem]">
              Don&apos;t replace your driveway. Revive it.
            </h1>
            <p className="mt-6 max-w-lg text-lg leading-relaxed text-stone-wash/85">
              Transform tired, faded surfaces with professional restoration across Lancashire, Merseyside
              and Greater Manchester — without the disruption of a full replacement.
            </p>
            <SignatureCtas />
            <HeroPostcode />
          </div>
          <div className="relative">
            <BeforeAfterSlider
              before={MEDIA.beforeAfter.before}
              after={MEDIA.beforeAfter.after}
              caption={MEDIA.beforeAfter.caption}
            />
          </div>
        </div>
      </section>

      <WhyRestore />

      <section className="site-container py-20">
        <p className="section-eyebrow">Services</p>
        <h2 className="mt-2 font-display text-3xl font-semibold text-asphalt">Crafted surface restoration</h2>
        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {SERVICE_CARDS.map((s) => (
            <article
              key={s.slug}
              className="group flex flex-col overflow-hidden rounded-lg border border-stone-line bg-white shadow-sm transition hover:shadow-lift"
            >
              {(() => {
                const img = serviceMedia(s.slug);
                return img ? (
                  <StockImage asset={img} className="rounded-t-lg" sizes="(max-width: 640px) 100vw, 33vw" />
                ) : (
                  <div className="aspect-[4/3] bg-asphalt-900" role="img" aria-label={`${s.name} — image pending`} />
                );
              })()}
              <div className="flex flex-1 flex-col p-6">
                <h3 className="font-display text-xl font-semibold text-asphalt">{s.name}</h3>
                <p className="mt-2 flex-1 text-sm leading-relaxed text-asphalt/70">{s.blurb}</p>
                <Link href={s.href} className="mt-4 text-sm font-semibold text-restore-dark hover:underline">
                  View service →
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>

      <HowItWorks />
      <RestoreVsReplace />
      <CoverageChecker />

      <CommercialTeaser />
      <FaqSection />
      <FinalCta />
    </>
  );
}

function SignatureCtas() {
  return (
    <div className="mt-8 flex flex-wrap gap-3">
      <Link href="/quote" className="btn-primary">
        Get my instant quote
      </Link>
      <Link href="/services" className="btn-secondary border-white/25 bg-transparent text-white hover:bg-white/10">
        Explore our services
      </Link>
    </div>
  );
}

function WhyRestore() {
  const points = [
    "Improved kerb appeal without laying new hardstanding.",
    "Often less disruptive than full excavation and replacement.",
    "Professional washing, preparation and protective treatments.",
    "Regional teams based around Burscough with territory-aware pricing.",
  ];
  return (
    <section className="bg-stone-wash py-20">
      <div className="site-container grid gap-12 md:grid-cols-2 md:items-center">
        <div>
          <p className="section-eyebrow">Why restore?</p>
          <h2 className="mt-2 font-display text-3xl font-semibold text-asphalt">
            Why replace when you can restore?
          </h2>
          <p className="mt-4 text-asphalt/75">
            Where the underlying construction is sound, restoration can refresh appearance and protection.
            We will tell you honestly when replacement or heavier repairs are more appropriate.
          </p>
          <ul className="mt-6 space-y-3 text-sm text-asphalt/80">
            {points.map((p) => (
              <li key={p} className="flex gap-2 border-l-2 border-restore-green pl-3">
                {p}
              </li>
            ))}
          </ul>
        </div>
        <BeforeAfterSlider
          before={MEDIA.beforeAfter.before}
          after={MEDIA.beforeAfter.after}
          caption={MEDIA.beforeAfter.caption}
        />
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    "Get an instant provisional quotation online.",
    "Arrange verification and booking.",
    "We prepare the surface (wash visit where required).",
    "Protective restoration coating — enjoy the finished result.",
  ];
  return (
    <section className="border-y border-stone-line bg-white py-20">
      <div className="site-container">
        <p className="section-eyebrow">How it works</p>
        <h2 className="mt-2 font-display text-3xl font-semibold text-asphalt">A clear customer journey</h2>
        <ol className="mt-10 grid gap-6 md:grid-cols-4">
          {steps.map((step, i) => (
            <li key={step} className="border-t-2 border-restore-green pt-4">
              <span className="text-xs font-bold text-restore-dark">0{i + 1}</span>
              <p className="mt-2 text-sm leading-relaxed text-asphalt/80">{step}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

function RestoreVsReplace() {
  return (
    <section className="site-container py-20">
      <div className="grid gap-8 md:grid-cols-2">
        <div className="rounded-lg border border-restore-green/30 bg-restore-muted/40 p-8">
          <h2 className="font-display text-2xl font-semibold text-asphalt">Restoration may suit when…</h2>
          <ul className="mt-4 list-inside list-disc space-y-2 text-sm text-asphalt/80">
            <li>Surface is faded but structurally sound.</li>
            <li>Moss, algae or cosmetic wear are the main issues.</li>
            <li>You want to refresh without full dig-out.</li>
          </ul>
        </div>
        <div className="rounded-lg border border-stone-line bg-white p-8">
          <h2 className="font-display text-2xl font-semibold text-asphalt">Further work may be needed when…</h2>
          <ul className="mt-4 list-inside list-disc space-y-2 text-sm text-asphalt/80">
            <li>Significant base failure or widespread structural cracking.</li>
            <li>Unsuitable or failed previous coatings.</li>
            <li>Drainage or levels need major correction.</li>
          </ul>
        </div>
      </div>
    </section>
  );
}

function CommercialTeaser() {
  return (
    <section className="bg-asphalt py-20 text-stone-wash">
      <div className="site-container flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="section-eyebrow text-restore-green">Commercial</p>
          <h2 className="mt-2 font-display text-3xl font-semibold">Car parks, forecourts & business sites</h2>
          <p className="mt-3 max-w-xl text-stone-wash/80">
            Dedicated commercial enquiries for retail parks, industrial estates, hotels and managing agents.
          </p>
        </div>
        <Link href="/commercial" className="btn-primary bg-white text-asphalt hover:bg-stone-wash">
          Commercial enquiry
        </Link>
      </div>
    </section>
  );
}

function FaqSection() {
  return (
    <section className="site-container py-20" id="faq">
      <p className="section-eyebrow">FAQ</p>
      <h2 className="mt-2 font-display text-3xl font-semibold text-asphalt">Straight answers</h2>
      <dl className="mt-10 space-y-6">
        {FAQ_ITEMS.map((item) => (
          <div key={item.q} className="border-b border-stone-line pb-6">
            <dt className="font-semibold text-asphalt">{item.q}</dt>
            <dd className="mt-2 text-sm leading-relaxed text-asphalt/75">{item.a}</dd>
          </div>
        ))}
      </dl>
      <Link href="/faq" className="mt-6 inline-block text-sm font-semibold text-restore-dark">
        Full FAQ →
      </Link>
    </section>
  );
}

function FinalCta() {
  return (
    <section className="border-t border-stone-line bg-stone-wash py-20">
      <div className="site-container text-center">
        <h2 className="font-display text-3xl font-semibold text-asphalt">Ready to revive your driveway?</h2>
        <p className="mx-auto mt-3 max-w-lg text-asphalt/70">
          Start with your postcode and measurements — provisional pricing uses your live pricing engine.
        </p>
        <Link href="/quote" className="btn-primary mt-8">
          Get my instant quote
        </Link>
      </div>
    </section>
  );
}