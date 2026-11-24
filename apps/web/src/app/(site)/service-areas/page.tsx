import Link from "next/link";

const regionalPages = [
  { href: "/areas/tarmac-restoration-blackpool", label: "Tarmac restoration Blackpool" },
  { href: "/areas/driveway-restoration-liverpool", label: "Driveway restoration Liverpool" },
  { href: "/areas/tarmac-restoration-manchester", label: "Tarmac restoration Manchester" },
  { href: "/areas/driveway-restoration-southport", label: "Driveway restoration Southport" },
  { href: "/areas/tarmac-restoration-preston", label: "Tarmac restoration Preston" },
];

const territories = [
  "West Lancashire (Burscough, Ormskirk, Skelmersdale)",
  "Sefton and Southport",
  "Liverpool and Merseyside",
  "Preston and Central Lancashire",
  "Blackpool and Fylde Coast",
  "Chorley and Wigan",
  "Blackburn and East Lancashire",
  "Bolton and Greater Manchester",
  "Warrington and surrounding areas",
];

export const metadata = { title: "Service areas" };

export default function ServiceAreasPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <h1 className="text-3xl font-semibold text-emerald-950">Where we work</h1>
      <p className="mt-3 max-w-3xl text-emerald-900/80">
        Revive My Drive operates across configurable territories in North West England. Travel,
        minimum job values and availability vary by region to keep work profitable and efficient.
      </p>
      <ul className="mt-8 grid gap-3 md:grid-cols-2">
        {territories.map((t) => (
          <li key={t} className="rounded-lg border bg-white px-4 py-3 text-sm">
            {t}
          </li>
        ))}
      </ul>
      <h2 className="mt-12 text-xl font-semibold">Regional guides</h2>
      <ul className="mt-4 space-y-2">
        {regionalPages.map((p) => (
          <li key={p.href}>
            <Link href={p.href} className="text-emerald-800 hover:underline">
              {p.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}