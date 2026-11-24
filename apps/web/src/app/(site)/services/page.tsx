import Link from "next/link";

const items = [
  { href: "/services/tarmac-restoration", title: "Tarmac restoration" },
  { href: "/services/block-paving", title: "Block paving restoration" },
  { href: "/services/imprinted-concrete", title: "Imprinted concrete restoration" },
  { href: "/services/commercial-car-parks", title: "Commercial car park restoration" },
  { href: "/services/minor-repairs", title: "Minor surface repairs" },
];

export const metadata = { title: "Services" };

export default function ServicesPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <h1 className="text-3xl font-semibold text-emerald-950">Restoration services</h1>
      <p className="mt-3 max-w-2xl text-emerald-900/80">
        We focus on restoring existing surfaces — cleaning, preparing and sealing rather than
        unnecessary full replacements. Most full restorations follow a two-visit workflow:
        pressure washing first, protective coating once the surface is dry and conditions are safe.
      </p>
      <ul className="mt-10 grid gap-4 md:grid-cols-2">
        {items.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className="block rounded-xl border bg-white p-6 shadow-sm hover:border-emerald-700"
            >
              <span className="text-lg font-medium text-emerald-950">{item.title}</span>
            </Link>
          </li>
        ))}
      </ul>
      <Link href="/quote" className="mt-10 inline-block text-emerald-800 font-semibold hover:underline">
        Get an instant provisional quote →
      </Link>
    </div>
  );
}