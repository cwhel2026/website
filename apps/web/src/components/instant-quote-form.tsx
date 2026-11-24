"use client";

import { useEffect, useState } from "react";
import { apiPost } from "@/lib/api";

type Service = { slug: string; name: string };

type Section = { label: string; length_m: string; width_m: string };

type QuotationResult = {
  reference: string;
  total_inc_vat_gbp: string | number;
  subtotal_ex_vat_gbp: string | number;
  estimated_contribution_gbp: string | number;
  requires_approval: boolean;
  provisional_disclaimer: string;
  status: string;
};

const SURFACE_TYPES = [
  { value: "tarmac", label: "Tarmac" },
  { value: "block_paving", label: "Block paving" },
  { value: "imprinted_concrete", label: "Imprinted concrete" },
  { value: "concrete", label: "Concrete" },
  { value: "other", label: "Other" },
];

const CONDITIONS = [
  { value: "good", label: "Good" },
  { value: "fair", label: "Fair" },
  { value: "poor", label: "Poor" },
  { value: "heavily_degraded", label: "Heavily degraded" },
];

export function InstantQuoteForm() {
  const [services, setServices] = useState<Service[]>([]);
  const [sections, setSections] = useState<Section[]>([
    { label: "Main driveway", length_m: "", width_m: "" },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QuotationResult | null>(null);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/services`)
      .then((r) => r.json())
      .then(setServices)
      .catch(() => setServices([]));
  }, []);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    const form = new FormData(e.currentTarget);
    const payload = {
      full_name: String(form.get("full_name")),
      email: String(form.get("email")),
      phone: String(form.get("phone") || "") || null,
      address_line1: String(form.get("address_line1")),
      address_line2: String(form.get("address_line2") || "") || null,
      town: String(form.get("town")),
      postcode: String(form.get("postcode")),
      service_slug: String(form.get("service_slug")),
      surface_type: String(form.get("surface_type")),
      surface_condition: String(form.get("surface_condition")),
      requires_washing: form.get("requires_washing") === "on",
      customer_washed_already: form.get("customer_washed_already") === "on",
      consent_service_messages: true,
      consent_marketing: form.get("consent_marketing") === "on",
      sections: sections.map((s) => ({
        label: s.label,
        length_m: s.length_m ? Number(s.length_m) : null,
        width_m: s.width_m ? Number(s.width_m) : null,
      })),
      source: "website",
    };
    try {
      const data = await apiPost<QuotationResult>("/api/v1/quotations/instant", payload);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Quotation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-semibold text-emerald-950">Instant provisional quotation</h1>
      <p className="mt-2 text-emerald-900/70">
        Measure your driveway in sections (length × width). Prices are provisional until we verify
        on site.
      </p>

      <form onSubmit={onSubmit} className="mt-8 space-y-6 rounded-2xl border bg-white p-6 shadow-sm">
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block text-sm">
            Full name
            <input name="full_name" required className="mt-1 w-full rounded-lg border px-3 py-2" />
          </label>
          <label className="block text-sm">
            Email
            <input name="email" type="email" required className="mt-1 w-full rounded-lg border px-3 py-2" />
          </label>
          <label className="block text-sm">
            Telephone
            <input name="phone" className="mt-1 w-full rounded-lg border px-3 py-2" />
          </label>
          <label className="block text-sm">
            Postcode
            <input name="postcode" required className="mt-1 w-full rounded-lg border px-3 py-2" />
          </label>
        </div>

        <label className="block text-sm">
          Address line 1
          <input name="address_line1" required className="mt-1 w-full rounded-lg border px-3 py-2" />
        </label>
        <label className="block text-sm">
          Address line 2
          <input name="address_line2" className="mt-1 w-full rounded-lg border px-3 py-2" />
        </label>
        <label className="block text-sm">
          Town
          <input name="town" required className="mt-1 w-full rounded-lg border px-3 py-2" />
        </label>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="block text-sm">
            Service
            <select name="service_slug" required className="mt-1 w-full rounded-lg border px-3 py-2">
              {services.map((s) => (
                <option key={s.slug} value={s.slug}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            Surface type
            <select name="surface_type" className="mt-1 w-full rounded-lg border px-3 py-2">
              {SURFACE_TYPES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            Condition
            <select name="surface_condition" className="mt-1 w-full rounded-lg border px-3 py-2">
              {CONDITIONS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <fieldset className="space-y-3">
          <legend className="text-sm font-semibold">Driveway sections</legend>
          {sections.map((section, index) => (
            <div key={index} className="grid gap-2 rounded-lg border p-3 md:grid-cols-4">
              <input
                aria-label="Section label"
                value={section.label}
                onChange={(e) => {
                  const next = [...sections];
                  next[index].label = e.target.value;
                  setSections(next);
                }}
                className="rounded border px-2 py-1 md:col-span-2"
              />
              <input
                aria-label="Length metres"
                placeholder="Length (m)"
                value={section.length_m}
                onChange={(e) => {
                  const next = [...sections];
                  next[index].length_m = e.target.value;
                  setSections(next);
                }}
                className="rounded border px-2 py-1"
              />
              <input
                aria-label="Width metres"
                placeholder="Width (m)"
                value={section.width_m}
                onChange={(e) => {
                  const next = [...sections];
                  next[index].width_m = e.target.value;
                  setSections(next);
                }}
                className="rounded border px-2 py-1"
              />
            </div>
          ))}
          <button
            type="button"
            className="text-sm font-medium text-emerald-800"
            onClick={() => setSections([...sections, { label: `Section ${sections.length + 1}`, length_m: "", width_m: "" }])}
          >
            + Add section
          </button>
        </fieldset>

        <div className="flex flex-wrap gap-4 text-sm">
          <label className="flex items-center gap-2">
            <input name="requires_washing" type="checkbox" defaultChecked />
            Include pressure washing
          </label>
          <label className="flex items-center gap-2">
            <input name="customer_washed_already" type="checkbox" />
            Already washed (coating only)
          </label>
          <label className="flex items-center gap-2">
            <input name="consent_marketing" type="checkbox" />
            Email updates about offers
          </label>
        </div>

        {error && <p className="text-sm text-red-700">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="rounded-full bg-emerald-900 px-6 py-3 font-semibold text-white disabled:opacity-50"
        >
          {loading ? "Calculating…" : "Calculate provisional quote"}
        </button>
      </form>

      {result && (
        <div className="mt-8 rounded-2xl border border-emerald-200 bg-emerald-50 p-6">
          <h2 className="text-xl font-semibold text-emerald-950">Reference {result.reference}</h2>
          <p className="mt-2 text-3xl font-bold text-emerald-900">
            £{Number(result.total_inc_vat_gbp).toFixed(2)}{" "}
            <span className="text-base font-normal">inc. VAT</span>
          </p>
          <p className="mt-2 text-sm text-emerald-900/80">
            Ex VAT: £{Number(result.subtotal_ex_vat_gbp).toFixed(2)} · Status: {result.status}
            {result.requires_approval ? " · Requires owner approval" : ""}
          </p>
          <p className="mt-4 text-sm text-emerald-900/70">{result.provisional_disclaimer}</p>
        </div>
      )}
    </div>
  );
}