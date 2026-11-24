import Link from "next/link";

export const metadata = { title: "Commercial car park restoration" };

export default function CommercialCarParksPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-semibold text-emerald-950">Commercial car park restoration</h1>
      <p className="mt-4 text-emerald-900/80">
        Larger areas are quoted with commercial multipliers, staged access planning and contribution
        margin checks. High-value quotes may route to the approval centre.
      </p>
      <Link href="/quote" className="mt-8 inline-block rounded-full bg-emerald-900 px-6 py-3 text-white">
        Get provisional quote
      </Link>
    </div>
  );
}