import Link from "next/link";

export const metadata = { title: "Tarmac restoration" };

export default function TarmacRestorationPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-semibold text-emerald-950">Tarmac driveway restoration</h1>
      <p className="mt-4 text-emerald-900/80">
        Faded, moss-covered or tired tarmac can often be restored without full replacement. We
        pressure wash and apply specialist protective coatings when the surface base is sound.
      </p>
      <Link href="/quote" className="mt-8 inline-block rounded-full bg-emerald-900 px-6 py-3 text-white">
        Get provisional quote
      </Link>
    </div>
  );
}