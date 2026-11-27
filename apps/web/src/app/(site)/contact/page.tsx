import Link from "next/link";

export const metadata = {
  title: "Contact",
  description: "Start an instant estimate, or send a commercial enquiry. No unverified phone number is published.",
};

export default function ContactPage() {
  return (
    <div>
      <header className="bg-brand-ink text-white">
        <div className="site-container py-12 md:py-16">
          <p className="section-eyebrow text-brand-gold">Contact</p>
          <h1 className="mt-3 font-display text-4xl font-medium md:text-5xl">Start with the estimate.</h1>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/75">
            The instant estimate collects the details we need for a tarmac price. A booking request, callback or
            emailed estimate follows that price. None of those confirm an appointment.
          </p>
        </div>
      </header>
      <div className="site-container grid gap-6 py-12 md:grid-cols-2 md:py-16">
        <Link href="/quote" className="border border-brand-line bg-white p-6">
          <h2 className="font-display text-2xl font-medium">Homeowners</h2>
          <p className="mt-3 text-sm leading-relaxed text-brand-ink/75">
            Get an instant tarmac estimate. Photographs are optional. You can ask for a callback or an email from the
            estimate screen.
          </p>
          <span className="mt-6 inline-flex min-h-11 items-center text-sm font-semibold">Get my instant estimate</span>
        </Link>
        <Link href="/commercial" className="border border-brand-line bg-white p-6">
          <h2 className="font-display text-2xl font-medium">Businesses</h2>
          <p className="mt-3 text-sm leading-relaxed text-brand-ink/75">
            Car parks, forecourts and commercial yards. The enquiry form records the site. It does not confirm a
            booking or show a price.
          </p>
          <span className="mt-6 inline-flex min-h-11 items-center text-sm font-semibold">Commercial enquiry</span>
        </Link>
        <p className="text-sm leading-relaxed text-brand-ink/70 md:col-span-2">
          A public telephone number and a postal address are not published yet. We will not invent them.
        </p>
      </div>
    </div>
  );
}
