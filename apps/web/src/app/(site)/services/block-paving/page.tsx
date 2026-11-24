import Link from "next/link";

export const metadata = { title: "Block paving restoration" };

export default function BlockPavingPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-semibold text-emerald-950">Block paving cleaning, sanding and sealing</h1>
      <p className="mt-4 text-emerald-900/80">
        Weeds, joint sand loss and surface dullness respond well to professional cleaning and
        sealing when blocks are stable.
      </p>
      <Link href="/quote" className="mt-8 inline-block rounded-full bg-emerald-900 px-6 py-3 text-white">
        Get provisional quote
      </Link>
    </div>
  );
}