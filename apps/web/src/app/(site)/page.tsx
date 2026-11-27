import Link from "next/link";
import Image from "next/image";
import { CoverageChecker } from "@/components/home/coverage-checker";
import { StockImage } from "@/components/site/stock-image";
import { TransformationGallery } from "@/components/site/transformation-gallery";
import { FAQ_ITEMS, HOW_IT_WORKS, SERVICE_CARDS, WHY_RESTORE } from "@/lib/site-content";
import { MEDIA, serviceMedia } from "@/lib/media-assets";
import { publicBrand } from "@/lib/public-brand";

export default function HomePage() {
  return (
    <>
      <Hero />
      <Transformations />
      <Services />
      <WhyRestore />
      <HowItWorks />
      <Coverage />
      <FaqSection />
      <FinalCta />
    </>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden bg-brand-ink text-white">
      <div className="absolute inset-0">
        <picture className="absolute inset-0 block">
          {MEDIA.hero.srcAvif ? <source srcSet={MEDIA.hero.srcAvif} type="image/avif" /> : null}
          <source srcSet={MEDIA.hero.srcWebp} type="image/webp" />
          <Image
            src={MEDIA.hero.srcWebp}
            alt={MEDIA.hero.alt}
            fill
            priority
            className="object-cover object-[center_62%]"
            sizes="100vw"
          />
        </picture>
        <div className="absolute inset-0 bg-gradient-to-t from-brand-ink via-brand-ink/85 to-brand-ink/50 sm:bg-gradient-to-r sm:from-brand-ink sm:via-brand-ink/75 sm:to-brand-ink/35" />
      </div>
      <div className="site-container relative flex flex-col justify-center py-8 sm:min-h-[70vh] sm:py-16">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-brand-gold">{publicBrand.tagline}</p>
        <h1 className="mt-3 max-w-xl font-display text-[2.15rem] font-medium leading-[1.02] sm:text-6xl sm:leading-[0.98]">
          Don’t replace it. Restore it.
        </h1>
        <p className="mt-4 max-w-lg text-sm leading-relaxed text-white/85 sm:mt-5 sm:text-lg">
          Transform your tired driveway with professional surface restoration, without the expense and disruption of
          a complete replacement.
        </p>
        <div className="mt-7 flex flex-col gap-3 sm:flex-row">
          <Link href="/quote" className="btn-primary">
            Get my instant estimate
          </Link>
          <Link href="/services" className="btn-on-dark">
            Explore our services
          </Link>
        </div>
      </div>
    </section>
  );
}

function Transformations() {
  return (
    <section className="site-container py-14 md:py-20" id="transformations">
      <div className="grid gap-8 lg:grid-cols-[0.8fr_1.2fr] lg:items-start">
        <div>
          <p className="section-eyebrow">Transformations</p>
          <h2 className="mt-3 font-display text-3xl font-medium leading-tight md:text-4xl">
            The same driveway. A clearer surface.
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-brand-ink/75">
            Drag the comparison. Each pair is the same surface, before and after restoration.
          </p>
        </div>
        <TransformationGallery />
      </div>
      <Link href="/transformations" className="mt-6 inline-flex min-h-11 items-center text-sm font-semibold">
        See the transformations
      </Link>
    </section>
  );
}

function Services() {
  return (
    <section className="border-y border-brand-line bg-white py-14 md:py-20">
      <div className="site-container">
        <p className="section-eyebrow">Our services</p>
        <h2 className="mt-3 max-w-xl font-display text-3xl font-medium md:text-4xl">
          Restoration for the surface you already have.
        </h2>
        <div className="mt-10 grid gap-px bg-brand-line sm:grid-cols-2 lg:grid-cols-3">
          {SERVICE_CARDS.map((service) => {
            const image = serviceMedia(service.slug);
            return (
              <article key={service.slug} className="flex flex-col bg-white">
                {image ? (
                  <StockImage asset={image} aspect="aspect-[16/10]" sizes="(max-width: 1024px) 100vw, 33vw" />
                ) : (
                  <p
                    className="flex aspect-[16/10] items-end bg-brand-ink p-4 text-xs uppercase tracking-[0.14em] text-white/70"
                    role="img"
                    aria-label={`${service.name}. Verified photography is not approved yet.`}
                  >
                    Photograph pending approval
                  </p>
                )}
                <div className="flex flex-1 flex-col p-5">
                  <h3 className="font-display text-2xl font-medium">{service.name}</h3>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-brand-ink/70">{service.blurb}</p>
                  <Link href={service.href} className="mt-4 inline-flex min-h-11 items-center text-sm font-semibold">
                    View service
                  </Link>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function WhyRestore() {
  return (
    <section className="site-container py-14 md:py-20">
      <p className="section-eyebrow">Why restore rather than replace?</p>
      <h2 className="mt-3 max-w-2xl font-display text-3xl font-medium md:text-4xl">
        Keep a sound driveway. Refresh what people see.
      </h2>
      <p className="mt-4 max-w-2xl text-sm leading-relaxed text-brand-ink/75">
        Restoration can suit a driveway whose construction is still sound. It is not a promise that every surface can
        be saved, and it is not a guaranteed saving against replacement.
      </p>
      <ul className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {WHY_RESTORE.map((point) => (
          <li key={point} className="border-t-2 border-brand-gold pt-4 text-sm font-medium leading-relaxed">
            {point}
          </li>
        ))}
      </ul>
    </section>
  );
}

function HowItWorks() {
  return (
    <section className="bg-brand-ink py-14 text-white md:py-20" id="how-it-works">
      <div className="site-container">
        <p className="section-eyebrow text-brand-gold">How it works</p>
        <h2 className="mt-3 font-display text-3xl font-medium md:text-4xl">Four steps. No surprise visit.</h2>
        <ol className="mt-10 grid gap-8 md:grid-cols-4">
          {HOW_IT_WORKS.map((step, index) => (
            <li key={step.title}>
              <p className="font-display text-3xl text-brand-gold">0{index + 1}</p>
              <p className="mt-3 font-semibold">{step.title}</p>
              <p className="mt-2 text-sm leading-relaxed text-white/70">{step.detail}</p>
            </li>
          ))}
        </ol>
        <p className="mt-8 max-w-2xl text-sm leading-relaxed text-white/70">
          Coating appointments depend on suitable weather and surface conditions.
        </p>
        <Link href="/how-it-works" className="btn-on-dark mt-6">
          Read the process
        </Link>
      </div>
    </section>
  );
}

function Coverage() {
  return (
    <section className="site-container py-14 md:py-20" id="coverage">
      <p className="section-eyebrow">Areas we cover</p>
      <h2 className="mt-3 max-w-2xl font-display text-3xl font-medium md:text-4xl">
        {publicBrand.coverageAreas}.
      </h2>
      <p className="mt-4 max-w-2xl text-sm leading-relaxed text-brand-ink/75">
        Check a postcode before you start an estimate. We do not advertise a public office.
      </p>
      <div className="mt-8">
        <CoverageChecker />
      </div>
    </section>
  );
}

function FaqSection() {
  return (
    <section className="border-t border-brand-line bg-white py-14 md:py-20" id="faq">
      <div className="site-container">
        <p className="section-eyebrow">Questions</p>
        <h2 className="mt-3 font-display text-3xl font-medium md:text-4xl">Before you ask us to call.</h2>
        <dl className="mt-8 divide-y divide-brand-line border-y border-brand-line">
          {FAQ_ITEMS.map((item) => (
            <div key={item.q} className="py-5">
              <dt className="font-semibold">{item.q}</dt>
              <dd className="mt-2 max-w-3xl text-sm leading-relaxed text-brand-ink/75">{item.a}</dd>
            </div>
          ))}
        </dl>
        <Link href="/faq" className="mt-6 inline-flex min-h-11 items-center text-sm font-semibold">
          All questions
        </Link>
      </div>
    </section>
  );
}

function FinalCta() {
  return (
    <section className="bg-brand-gold text-brand-ink">
      <div className="site-container py-16 md:py-20">
        <h2 className="max-w-xl font-display text-4xl font-medium leading-[1.02] md:text-5xl">
          Give your driveway a second life.
        </h2>
        <p className="mt-4 text-lg">Get your free instant estimate today.</p>
        <Link href="/quote" className="mt-8 inline-flex min-h-12 items-center bg-brand-ink px-6 py-3.5 text-sm font-semibold text-white">
          Get my instant estimate
        </Link>
      </div>
    </section>
  );
}
