import Link from "next/link";
import { notFound } from "next/navigation";

const CONTENT: Record<string, { title: string; intro: string; bullets: string[] }> = {
  "tarmac-restoration-blackpool": {
    title: "Tarmac restoration in Blackpool and the Fylde Coast",
    intro:
      "Coastal weather, salt air and high traffic can fade and fatigue tarmac driveways and car park surfaces. We restore existing tarmac with professional washing and protective coatings.",
    bullets: [
      "Serving Blackpool, Lytham, St Annes, Fleetwood and Thornton-Cleveleys",
      "Provisional online quotes with territory-specific travel estimates",
      "Two-stage restoration when washing and coating are required",
    ],
  },
  "driveway-restoration-liverpool": {
    title: "Driveway restoration in Liverpool and Merseyside",
    intro:
      "From Victorian terraces to modern developments, we restore tarmac, block paving and imprinted concrete without unnecessary excavation.",
    bullets: [
      "Covering Liverpool, Wirral-access routes, Knowsley and St Helens",
      "Measurement support for irregular or split-level driveways",
      "Coating appointments planned around drying time and local weather",
    ],
  },
  "tarmac-restoration-manchester": {
    title: "Tarmac restoration in Greater Manchester",
    intro:
      "Greater Manchester properties often combine heavy vehicle use with limited drying time between rain showers. Our scheduling engine groups work to reduce travel where possible.",
    bullets: [
      "Bolton, Bury, Salford, Trafford, Stockport and surrounding districts",
      "Higher minimum job values may apply for distant single visits",
      "Commercial forecourts and car parks quoted separately",
    ],
  },
  "driveway-restoration-southport": {
    title: "Driveway restoration in Southport and Sefton",
    intro:
      "Southport and coastal Sefton properties benefit from restoration rather than replacement when the base is sound. We assess moss, algae and surface breakdown on site.",
    bullets: [
      "Southport, Formby, Crosby, Maghull and Ainsdale",
      "Headquartered in West Lancashire for efficient local routing",
      "Online provisional quotes available 24/7",
    ],
  },
  "tarmac-restoration-preston": {
    title: "Tarmac restoration in Preston and Central Lancashire",
    intro:
      "Central Lancashire driveways and commercial bays can be restored with colour-enhancing coatings after thorough preparation.",
    bullets: [
      "Preston, Leyland, Penwortham, Longton and Garstang",
      "Configurable pricing — no hardcoded final prices",
      "Approval centre for complex or low-margin quotations",
    ],
  },
};

export function generateStaticParams() {
  return Object.keys(CONTENT).map((slug) => ({ slug }));
}

export default async function AreaPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const page = CONTENT[slug];
  if (!page) notFound();

  return (
    <article className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-semibold text-emerald-950">{page.title}</h1>
      <p className="mt-4 text-emerald-900/80">{page.intro}</p>
      <ul className="mt-6 list-disc space-y-2 pl-5 text-emerald-900/80">
        {page.bullets.map((b) => (
          <li key={b}>{b}</li>
        ))}
      </ul>
      <Link
        href="/quote"
        className="mt-10 inline-block rounded-full bg-emerald-900 px-6 py-3 font-semibold text-white"
      >
        Get a provisional quote
      </Link>
    </article>
  );
}