import Link from "next/link";

const services = [
  "Tarmac driveway restoration",
  "Block paving cleaning and sealing",
  "Pattern imprinted concrete restoration",
  "Commercial car park restoration",
  "Pressure washing and protective coatings",
];

export default function HomePage() {
  return (
    <>
      <section className="relative overflow-hidden bg-gradient-to-br from-emerald-950 via-emerald-900 to-emerald-800 text-white">
        <div className="mx-auto max-w-6xl px-4 py-20 md:py-28">
          <p className="text-sm font-medium uppercase tracking-widest text-emerald-200/90">
            North West England surface specialists
          </p>
          <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-tight md:text-5xl">
            Restore existing driveways and exterior surfaces — without replacing them
          </h1>
          <p className="mt-6 max-w-2xl text-lg text-emerald-50/90">
            Revive My Drive helps homeowners and businesses bring tired tarmac, block paving
            and imprinted concrete back to life with professional washing, preparation and
            protective restoration coatings.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              href="/quote"
              className="rounded-full bg-amber-400 px-6 py-3 font-semibold text-emerald-950 hover:bg-amber-300"
            >
              Get an instant provisional quote
            </Link>
            <Link
              href="/services"
              className="rounded-full border border-white/30 px-6 py-3 font-medium hover:bg-white/10"
            >
              View services
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16">
        <h2 className="text-2xl font-semibold text-emerald-950">What we restore</h2>
        <ul className="mt-6 grid gap-3 md:grid-cols-2">
          {services.map((s) => (
            <li
              key={s}
              className="rounded-xl border border-emerald-900/10 bg-white px-5 py-4 shadow-sm"
            >
              {s}
            </li>
          ))}
        </ul>
      </section>

      <section className="bg-white py-16">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-2xl font-semibold text-emerald-950">How instant quotation works</h2>
          <ol className="mt-8 grid gap-6 md:grid-cols-3">
            {[
              "Enter your address, surface type and measurements (multiple sections supported).",
              "Receive a provisional price with labour, materials and travel estimates.",
              "Book a verification visit — complex or low-margin jobs go to the approval centre.",
            ].map((step, i) => (
              <li key={step} className="rounded-xl border border-emerald-900/10 p-6">
                <span className="text-sm font-semibold text-emerald-700">Step {i + 1}</span>
                <p className="mt-2 text-emerald-950/80">{step}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>
    </>
  );
}