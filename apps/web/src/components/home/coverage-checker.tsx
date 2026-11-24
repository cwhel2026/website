"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { PRIORITY_TOWNS } from "@/lib/site-content";

type Territory = {
  code: string;
  name: string;
  localities: { name: string }[];
};

export function CoverageChecker() {
  const [territories, setTerritories] = useState<Territory[]>([]);
  const [postcode, setPostcode] = useState("");
  const [result, setResult] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Territory[]>("/api/v1/territories")
      .then(setTerritories)
      .catch(() => setTerritories([]));
  }, []);

  async function check(e: React.FormEvent) {
    e.preventDefault();
    setResult(null);
    try {
      const data = await apiGet<{ covered: boolean; territory_name?: string; message?: string }>(
        `/api/v1/public/coverage?postcode=${encodeURIComponent(postcode.trim())}`,
      );
      if (data.covered) {
        setResult(`Good news — ${postcode.toUpperCase()} is in our ${data.territory_name} operating area.`);
      } else {
        setResult(data.message ?? "We could not confirm coverage for this postcode yet.");
      }
    } catch {
      setResult("Unable to check coverage right now. You can still start a quotation.");
    }
  }

  const localityNames = new Set(
    territories.flatMap((t) => t.localities.map((l) => l.name)),
  );

  return (
    <section className="bg-white py-20" id="areas">
      <div className="site-container">
        <p className="section-eyebrow">Regional coverage</p>
        <h2 className="mt-2 font-display text-3xl font-semibold text-asphalt md:text-4xl">
          Serving the North West from Lancashire HQ
        </h2>
        <p className="mt-4 max-w-2xl text-asphalt/75">
          Territories A–I are configured in your operating system — we match postcodes to real coverage
          areas rather than guessing from a static map.
        </p>

        <form onSubmit={check} className="mt-8 flex max-w-md flex-col gap-2 sm:flex-row">
          <input
            value={postcode}
            onChange={(e) => setPostcode(e.target.value)}
            placeholder="Postcode"
            className="flex-1 rounded-md border border-stone-line px-4 py-3"
            required
          />
          <button type="submit" className="btn-primary">
            Check postcode
          </button>
        </form>
        {result && <p className="mt-3 text-sm font-medium text-restore-dark">{result}</p>}

        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          <div
            aria-hidden
            className="relative min-h-[220px] overflow-hidden rounded-lg border border-stone-line bg-gradient-to-br from-asphalt-900 via-asphalt-800 to-restore-dark/90"
          >
            <div className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_30%_40%,#3d8f6c_0%,transparent_55%)]" />
            <p className="absolute bottom-4 left-4 right-4 text-sm text-white/80">
              Illustrative map — live coverage is determined by configured postcode districts.
            </p>
          </div>
          <ul className="flex flex-wrap gap-2 text-sm">
            {PRIORITY_TOWNS.map((town) => (
              <li
                key={town}
                className={`rounded-full border px-3 py-1 ${
                  localityNames.has(town) ? "border-restore-green/40 bg-restore-muted/50" : "border-stone-line"
                }`}
              >
                {town}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}