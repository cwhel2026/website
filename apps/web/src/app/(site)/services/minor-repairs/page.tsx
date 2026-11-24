import Link from "next/link";

export const metadata = { title: "Minor surface repairs" };

export default function MinorRepairsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-semibold text-emerald-950">Minor surface repairs</h1>
      <p className="mt-4 text-emerald-900/80">
        Localised tarmac repairs, oil stain treatment and edge make-good work — scoped on site after
        photographs and measurements.
      </p>
      <Link href="/quote" className="mt-8 inline-block rounded-full bg-emerald-900 px-6 py-3 text-white">
        Get provisional quote
      </Link>
    </div>
  );
}