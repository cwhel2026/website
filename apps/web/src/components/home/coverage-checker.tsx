"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import { publicBrand } from "@/lib/public-brand";
import { LOCAL_PAGES, PRIORITY_TOWNS } from "@/lib/site-content";

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
        setResult(`${postcode.toUpperCase()} is within the area we can quote.`);
      } else {
        setResult(data.message ?? "We could not confirm this postcode yet. You can still start an estimate.");
      }
    } catch {
      setResult("The coverage check is unavailable right now. You can still start an estimate.");
    }
  }

  const localityNames = new Set(territories.flatMap((territory) => territory.localities.map((item) => item.name)));

  return (
    <div>
      <form onSubmit={check} className="flex max-w-lg flex-col gap-2 sm:flex-row">
        <label className="sr-only" htmlFor="coverage-postcode">
          Postcode
        </label>
        <input
          id="coverage-postcode"
          value={postcode}
          onChange={(e) => setPostcode(e.target.value)}
          placeholder="Postcode"
          className="min-h-12 flex-1 border border-brand-line bg-white px-4 text-base"
          required
        />
        <button type="submit" className="btn-primary">
          Check postcode
        </button>
      </form>
      {result ? <p className="mt-3 text-sm font-medium text-brand-ink">{result}</p> : null}

      <ul className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {publicBrand.counties.map((county) => (
          <li key={county} className="border border-brand-line bg-white px-4 py-4 text-sm font-medium">
            {county}
          </li>
        ))}
        <li className="border border-brand-line bg-white px-4 py-4 text-sm font-medium">Surrounding areas</li>
      </ul>

      <ul className="mt-6 flex flex-wrap gap-2 text-sm">
        {PRIORITY_TOWNS.map((town) => (
          <li
            key={town}
            className={`border px-3 py-1.5 ${
              localityNames.has(town) ? "border-brand-ink bg-brand-ink text-white" : "border-brand-line bg-white"
            }`}
          >
            {town}
          </li>
        ))}
      </ul>

      <ul className="mt-8 space-y-2 text-sm">
        {LOCAL_PAGES.map((page) => (
          <li key={page.slug}>
            <Link href={`/areas/${page.slug}`} className="font-semibold text-brand-ink underline-offset-4 hover:underline">
              {page.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
