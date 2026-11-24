import Link from "next/link";

export const metadata = { title: "Imprinted concrete restoration" };

export default function ImprintedConcretePage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-semibold text-emerald-950">Pattern imprinted concrete restoration</h1>
      <p className="mt-4 text-emerald-900/80">
        Colour-faded imprinted concrete can be revived with careful preparation and compatible
        colour-enhancing treatments.
      </p>
      <Link href="/quote" className="mt-8 inline-block rounded-full bg-emerald-900 px-6 py-3 text-white">
        Get provisional quote
      </Link>
    </div>
  );
}