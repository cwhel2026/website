import Link from "next/link";
import { publicBrand } from "@/lib/public-brand";

const regionalPages = [
  { href: "/areas/tarmac-restoration-blackpool", label: "Tarmac restoration Blackpool" },
  { href: "/areas/driveway-restoration-liverpool", label: "Driveway restoration Liverpool" },
  { href: "/areas/tarmac-restoration-manchester", label: "Tarmac restoration Manchester" },
  { href: "/areas/driveway-restoration-southport", label: "Driveway restoration Southport" },
  { href: "/areas/tarmac-restoration-preston", label: "Tarmac restoration Preston" },
];

const territories = [
  "Lancashire (West Lancashire, Central Lancashire, East Lancashire, Fylde Coast)",
  "Greater Manchester",
  "Merseyside",
  "Cheshire and Warrington",
  "Cumbria (south)",
  "West Yorkshire (border areas)",
  "Surrounding North West postcodes where travel remains efficient",
];

export const metadata = { title: "Service areas" };

export default function ServiceAreasPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <h1 className="text-3xl font-semibold text-emerald-950">Where we work</h1>
      <p className="mt-3 max-w-3xl text-emerald-900/80">
        {publicBrand.tradingName} serves customers across {publicBrand.coverageAreas}. Online quotes check
        postcode coverage and travel from our operational scheduling base in Central Lancashire — we do not
        advertise Preston as our public office location. Minimum job values and availability vary by region.
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