"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { apiGet, apiPost } from "@/lib/api";
import { trackFunnel, getStoredUtm } from "@/lib/analytics";

const STORAGE_KEY = "rmd_quote_draft";
const STEPS = ["Location", "Surface", "Measurements", "Condition", "Preparation", "Quote", "Contact"];

type Service = { slug: string; name: string };
type Section = { label: string; length_m: string; width_m: string; area_sqm: string };

type QuoteState = {
  postcode: string;
  town: string;
  covered: boolean | null;
  territoryName: string;
  service_slug: string;
  surface_type: string;
  surface_condition: string;
  sections: Section[];
  requires_washing: boolean;
  customer_washed_already: boolean;
  visible_damage: string;
  full_name: string;
  email: string;
  phone: string;
  address_line1: string;
  address_line2: string;
  consent_marketing: boolean;
  consent_service_messages: boolean;
};

type ProvisionalQuotation = {
  input_fingerprint: string;
  total_inc_vat_gbp: string | number | null;
  subtotal_ex_vat_gbp: string | number | null;
  vat_gbp?: string | number | null;
  requires_approval: boolean | null;
  provisional_disclaimer: string;
  surface_supported: boolean;
  unsupported_reason?: string | null;
  total_area_sqm?: string | number | null;
  breakdown?: { lines?: { label: string; amount_gbp?: number }[] };
};

type SavedQuotation = ProvisionalQuotation & {
  reference: string;
  status: string;
};

const SURFACE_TYPES = [
  { value: "tarmac", label: "Tarmac", hint: "Smooth or coarse tarmac drives and paths." },
  { value: "block_paving", label: "Block paving", hint: "Clay or concrete blocks." },
  { value: "imprinted_concrete", label: "Imprinted concrete", hint: "Pattern-stamped concrete." },
  { value: "concrete", label: "Concrete", hint: "Plain concrete slabs or drives." },
  { value: "other", label: "Not sure", hint: "We will confirm on site." },
];

const CONDITIONS = [
  { value: "good", label: "Good — light fading" },
  { value: "fair", label: "Fair — visible wear" },
  { value: "poor", label: "Poor — moss, stains or cracks" },
  { value: "heavily_degraded", label: "Heavily degraded" },
];

function defaultState(postcode = ""): QuoteState {
  return {
    postcode,
    town: "",
    covered: null,
    territoryName: "",
    service_slug: "tarmac-driveway-restoration",
    surface_type: "tarmac",
    surface_condition: "fair",
    sections: [{ label: "Main driveway", length_m: "", width_m: "", area_sqm: "" }],
    requires_washing: true,
    customer_washed_already: false,
    visible_damage: "",
    full_name: "",
    email: "",
    phone: "",
    address_line1: "",
    address_line2: "",
    consent_marketing: false,
    consent_service_messages: true,
  };
}

const IDEMPOTENCY_KEY = "rmd_quote_idempotency";

export function QuoteWizard() {
  const searchParams = useSearchParams();
  const [step, setStep] = useState(0);
  const [state, setState] = useState<QuoteState>(() => defaultState(searchParams.get("postcode") ?? ""));
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [provisional, setProvisional] = useState<ProvisionalQuotation | null>(null);
  const [saved, setSaved] = useState<SavedQuotation | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const pricingInputKey = useMemo(
    () =>
      JSON.stringify({
        postcode: state.postcode,
        town: state.town,
        service_slug: state.service_slug,
        surface_type: state.surface_type,
        surface_condition: state.surface_condition,
        sections: state.sections,
        requires_washing: state.requires_washing,
        customer_washed_already: state.customer_washed_already,
      }),
    [
      state.postcode,
      state.town,
      state.service_slug,
      state.surface_type,
      state.surface_condition,
      state.sections,
      state.requires_washing,
      state.customer_washed_already,
    ],
  );

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) setState({ ...defaultState(), ...JSON.parse(raw) });
    } catch {
      /* ignore */
    }
    apiGet<Service[]>("/api/v1/services")
      .then(setServices)
      .catch(() => setServices([]));
    const fromUrl = searchParams.get("service");
    if (fromUrl) patch({ service_slug: fromUrl });
    void trackFunnel("quote_start", 0);
  }, [searchParams]);

  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  /** Session drafts may keep old marketing slugs (e.g. tarmac-restoration); align with the live catalogue. */
  useEffect(() => {
    if (services.length === 0) return;
    const slugs = new Set(services.map((s) => s.slug));
    if (slugs.has(state.service_slug)) return;
    const tarmac =
      services.find((s) => s.slug.includes("tarmac-driveway")) ??
      services.find((s) => s.slug.includes("tarmac"));
    const match =
      state.surface_type === "tarmac"
        ? tarmac
        : services.find((s) => s.slug.includes(state.surface_type.replace("_", "-")));
    patch({ service_slug: match?.slug ?? services[0].slug });
  }, [services, state.service_slug, state.surface_type]);

  useEffect(() => {
    setProvisional(null);
    setSaved(null);
  }, [pricingInputKey]);

  const totalSqm = useMemo(() => {
    return state.sections.reduce((sum, s) => {
      if (s.area_sqm) return sum + Number(s.area_sqm);
      const l = Number(s.length_m);
      const w = Number(s.width_m);
      if (l > 0 && w > 0) return sum + l * w;
      return sum;
    }, 0);
  }, [state.sections]);

  const patch = useCallback((p: Partial<QuoteState>) => setState((s) => ({ ...s, ...p })), []);

  async function checkCoverage() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<{ covered: boolean; territory_name?: string; message?: string }>(
        `/api/v1/public/coverage?postcode=${encodeURIComponent(state.postcode.trim())}&town=${encodeURIComponent(state.town)}`,
      );
      patch({
        covered: data.covered,
        territoryName: data.territory_name ?? "",
      });
      if (!data.covered) setError(data.message ?? "Outside current territories — we may still review your enquiry.");
    } catch {
      patch({ covered: null });
      setError("Could not verify coverage. You may continue.");
    } finally {
      setLoading(false);
    }
  }

  function buildSectionsPayload() {
    return state.sections.map((s) => ({
      label: s.label,
      length_m: s.length_m ? Number(s.length_m) : null,
      width_m: s.width_m ? Number(s.width_m) : null,
      area_sqm: s.area_sqm ? Number(s.area_sqm) : null,
    }));
  }

  function buildPricingPayload() {
    return {
      postcode: state.postcode,
      town: state.town || null,
      service_slug: state.service_slug,
      surface_type: state.surface_type,
      surface_condition: state.surface_condition,
      requires_washing: state.requires_washing,
      customer_washed_already: state.customer_washed_already,
      sections: buildSectionsPayload(),
    };
  }

  async function calculateProvisional() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiPost<ProvisionalQuotation>("/api/v1/quotations/provisional", buildPricingPayload());
      if (!data.surface_supported) {
        setError(data.unsupported_reason ?? "This surface is not supported for the selected service.");
        setProvisional(null);
        return;
      }
      if (data.total_inc_vat_gbp == null) {
        setError("Unable to calculate a price for these inputs.");
        return;
      }
      setProvisional(data);
      void trackFunnel("quote_estimate", 5);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Quotation could not be calculated.");
    } finally {
      setLoading(false);
    }
  }

  async function submitQuotation() {
    if (!provisional?.input_fingerprint) {
      setError("Calculate your estimate before submitting your details.");
      return;
    }
    setSubmitting(true);
    setError(null);
    const utm = getStoredUtm();
    let idempotencyKey = sessionStorage.getItem(IDEMPOTENCY_KEY);
    if (!idempotencyKey) {
      idempotencyKey = crypto.randomUUID();
      sessionStorage.setItem(IDEMPOTENCY_KEY, idempotencyKey);
    }
    const payload = {
      ...buildPricingPayload(),
      town: state.town || "Pending",
      full_name: state.full_name.trim(),
      email: state.email.trim(),
      phone: state.phone?.trim() || null,
      address_line1: state.address_line1.trim(),
      address_line2: state.address_line2?.trim() || null,
      visible_damage: state.visible_damage || null,
      consent_service_messages: state.consent_service_messages,
      consent_marketing: state.consent_marketing,
      input_fingerprint: provisional.input_fingerprint,
      idempotency_key: idempotencyKey,
      source: utm.source ?? "website",
      campaign: utm.campaign ?? null,
    };
    try {
      const data = await apiPost<SavedQuotation>("/api/v1/quotations/submit", payload);
      setSaved({ ...provisional, reference: data.reference, status: data.status });
      sessionStorage.removeItem(STORAGE_KEY);
      void trackFunnel("quote_complete", 6);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save your quotation.");
    } finally {
      setSubmitting(false);
    }
  }

  function next() {
    void trackFunnel("quote_step", step);
    if (step === 4 && totalSqm <= 0) {
      setError("Enter at least one measurement section before continuing.");
      return;
    }
    if (step === 5 && !provisional) void calculateProvisional();
    else setStep((s) => Math.min(s + 1, STEPS.length - 1));
  }

  function back() {
    setStep((s) => Math.max(s - 1, 0));
  }

  return (
    <div className="min-h-screen bg-stone-wash pb-24">
      <div className="site-container py-10 md:py-14">
        <p className="section-eyebrow">Instant quotation</p>
        <h1 className="mt-2 font-display text-3xl font-semibold text-asphalt md:text-4xl">
          Your provisional price in minutes
        </h1>

        <ol className="mt-8 flex gap-1 overflow-x-auto text-xs sm:text-sm" aria-label="Progress">
          {STEPS.map((label, i) => (
            <li
              key={label}
              className={`whitespace-nowrap rounded-full px-3 py-1.5 ${
                i === step ? "bg-asphalt text-white" : i < step ? "bg-restore-muted text-restore-dark" : "bg-white text-asphalt/50"
              }`}
            >
              {label}
            </li>
          ))}
        </ol>

        <div className="mt-8 rounded-lg border border-stone-line bg-white p-6 shadow-sm md:p-10">
          {step === 0 && (
            <StepLocation
              state={state}
              patch={patch}
              loading={loading}
              error={error}
              onCheck={checkCoverage}
            />
          )}
          {step === 1 && <StepSurface state={state} patch={patch} services={services} />}
          {step === 2 && (
            <StepMeasurements state={state} patch={patch} totalSqm={totalSqm} />
          )}
          {step === 3 && <StepCondition state={state} patch={patch} />}
          {step === 4 && <StepPrep state={state} patch={patch} />}
          {step === 5 && (
            <StepQuote
              result={provisional}
              loading={loading}
              error={error}
              onRecalc={() => void calculateProvisional()}
            />
          )}
          {step === 6 && (
            <StepContact
              state={state}
              patch={patch}
              provisional={provisional}
              saved={saved}
              submitting={submitting}
              error={error}
              onSubmit={() => void submitQuotation()}
            />
          )}

          <div className="mt-10 flex flex-wrap justify-between gap-3 border-t border-stone-line pt-6">
            <button type="button" onClick={back} disabled={step === 0} className="btn-secondary disabled:opacity-40">
              Back
            </button>
            {step < 6 && (
              <button
                type="button"
                onClick={next}
                disabled={step === 0 && !state.postcode.trim()}
                className="btn-primary"
              >
                {step === 5 && !provisional ? "Calculate estimate" : "Continue"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StepLocation({
  state,
  patch,
  loading,
  error,
  onCheck,
}: {
  state: QuoteState;
  patch: (p: Partial<QuoteState>) => void;
  loading: boolean;
  error: string | null;
  onCheck: () => void;
}) {
  return (
    <div>
      <h2 className="font-display text-xl font-semibold">Where is the property?</h2>
      <p className="mt-2 text-sm text-asphalt/70">We check live territory configuration — no guesswork.</p>
      <label className="mt-6 block text-sm font-medium">
        Postcode
        <input
          value={state.postcode}
          onChange={(e) => patch({ postcode: e.target.value.toUpperCase() })}
          className="mt-1 w-full rounded-md border border-stone-line px-4 py-3"
          autoComplete="postal-code"
          required
        />
      </label>
      <label className="mt-4 block text-sm font-medium">
        Town (optional)
        <input
          value={state.town}
          onChange={(e) => patch({ town: e.target.value })}
          className="mt-1 w-full rounded-md border border-stone-line px-4 py-3"
        />
      </label>
      <button type="button" className="btn-secondary mt-4" onClick={onCheck} disabled={loading || !state.postcode.trim()}>
        {loading ? "Checking…" : "Check coverage"}
      </button>
      {state.covered === true && (
        <p className="mt-3 text-sm text-restore-dark">Covered — {state.territoryName}</p>
      )}
      {error && <p className="mt-3 text-sm text-amber-800">{error}</p>}
    </div>
  );
}

function StepSurface({
  state,
  patch,
  services,
}: {
  state: QuoteState;
  patch: (p: Partial<QuoteState>) => void;
  services: Service[];
}) {
  return (
    <div>
      <h2 className="font-display text-xl font-semibold">Surface & service</h2>
      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        {SURFACE_TYPES.map((s) => (
          <button
            key={s.value}
            type="button"
            onClick={() => patch({ surface_type: s.value })}
            className={`rounded-lg border p-4 text-left transition ${
              state.surface_type === s.value ? "border-restore-green bg-restore-muted/50" : "border-stone-line"
            }`}
          >
            <span className="font-semibold">{s.label}</span>
            <span className="mt-1 block text-xs text-asphalt/65">{s.hint}</span>
          </button>
        ))}
      </div>
      <label className="mt-6 block text-sm font-medium">
        Service (from your active catalogue)
        <select
          value={state.service_slug}
          onChange={(e) => patch({ service_slug: e.target.value })}
          className="mt-1 w-full rounded-md border border-stone-line px-4 py-3"
        >
          {services.map((s) => (
            <option key={s.slug} value={s.slug}>
              {s.name}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}

function StepMeasurements({
  state,
  patch,
  totalSqm,
}: {
  state: QuoteState;
  patch: (p: Partial<QuoteState>) => void;
  totalSqm: number;
}) {
  function updateSection(i: number, field: keyof Section, value: string) {
    const sections = [...state.sections];
    sections[i] = { ...sections[i], [field]: value };
    patch({ sections });
  }

  return (
    <div>
      <h2 className="font-display text-xl font-semibold">Measurements</h2>
      <p className="mt-2 text-sm text-asphalt/70">
        Add rectangular sections or enter total m². Total estimate:{" "}
        <strong>{totalSqm > 0 ? `${totalSqm.toFixed(1)} m²` : "—"}</strong>
      </p>
      <div className="mt-4 rounded-lg border border-stone-line bg-stone-wash p-4 text-sm text-asphalt/75">
        <p className="font-semibold text-asphalt">Measurement guide</p>
        <p className="mt-1">
          Measure in metres along the longest edges. For L-shaped drives, split into separate rectangles.
          Final pricing may be adjusted after on-site verification.
        </p>
        <div className="mt-3 max-w-xs rounded border border-dashed border-asphalt/30 bg-white px-4 py-6 text-center text-xs text-asphalt/60">
          Length (m) × width (m) = area (m²)
        </div>
      </div>
      {state.sections.map((section, i) => (
        <div key={i} className="mt-4 grid gap-2 rounded-lg border border-stone-line p-4 md:grid-cols-4">
          <input
            aria-label="Section name"
            value={section.label}
            onChange={(e) => updateSection(i, "label", e.target.value)}
            className="rounded border px-3 py-2 md:col-span-2"
          />
          <input
            placeholder="Length (m)"
            inputMode="decimal"
            value={section.length_m}
            onChange={(e) => updateSection(i, "length_m", e.target.value)}
            className="rounded border px-3 py-2"
          />
          <input
            placeholder="Width (m)"
            inputMode="decimal"
            value={section.width_m}
            onChange={(e) => updateSection(i, "width_m", e.target.value)}
            className="rounded border px-3 py-2"
          />
          <input
            placeholder="Or area (m²)"
            inputMode="decimal"
            value={section.area_sqm}
            onChange={(e) => updateSection(i, "area_sqm", e.target.value)}
            className="rounded border px-3 py-2 md:col-span-4"
          />
        </div>
      ))}
      <button
        type="button"
        className="mt-3 text-sm font-semibold text-restore-dark"
        onClick={() =>
          patch({
            sections: [...state.sections, { label: `Section ${state.sections.length + 1}`, length_m: "", width_m: "", area_sqm: "" }],
          })
        }
      >
        + Add section
      </button>
    </div>
  );
}

function StepCondition({
  state,
  patch,
}: {
  state: QuoteState;
  patch: (p: Partial<QuoteState>) => void;
}) {
  return (
    <div>
      <h2 className="font-display text-xl font-semibold">Surface condition</h2>
      <ConditionRadios state={state} patch={patch} />
      <label className="mt-6 block text-sm">
        Notes on cracks, oil, moss or coatings (optional)
        <textarea
          value={state.visible_damage}
          onChange={(e) => patch({ visible_damage: e.target.value })}
          rows={3}
          className="mt-1 w-full rounded-md border border-stone-line px-3 py-2"
        />
      </label>
    </div>
  );
}

function ConditionRadios({
  state,
  patch,
}: {
  state: QuoteState;
  patch: (p: Partial<QuoteState>) => void;
}) {
  return (
    <div className="mt-4 space-y-2">
      {CONDITIONS.map((c) => (
        <label key={c.value} className="flex cursor-pointer items-center gap-3 rounded-lg border border-stone-line px-4 py-3">
          <input
            type="radio"
            name="condition"
            checked={state.surface_condition === c.value}
            onChange={() => patch({ surface_condition: c.value })}
          />
          {c.label}
        </label>
      ))}
    </div>
  );
}

function StepPrep({
  state,
  patch,
}: {
  state: QuoteState;
  patch: (p: Partial<QuoteState>) => void;
}) {
  return (
    <div>
      <h2 className="font-display text-xl font-semibold">Preparation</h2>
      <p className="mt-2 text-sm text-asphalt/70">
        Coatings need a clean surface. Washing is priced through your existing engine when selected.
      </p>
      <label className="mt-4 flex items-center gap-3">
        <input
          type="checkbox"
          checked={state.requires_washing}
          onChange={(e) => patch({ requires_washing: e.target.checked, customer_washed_already: false })}
        />
        Include professional pressure washing
      </label>
      <label className="mt-3 flex items-center gap-3">
        <input
          type="checkbox"
          checked={state.customer_washed_already}
          onChange={(e) =>
            patch({ customer_washed_already: e.target.checked, requires_washing: e.target.checked ? false : state.requires_washing })
          }
        />
        Already suitably washed — coating visit only
      </label>
    </div>
  );
}

function StepQuote({
  result,
  loading,
  error,
  onRecalc,
}: {
  result: ProvisionalQuotation | null;
  loading: boolean;
  error: string | null;
  onRecalc: () => void;
}) {
  if (loading) return <p className="text-center py-12 text-asphalt/70">Calculating your provisional estimate…</p>;
  if (error) return (
    <div>
      <p className="text-sm text-red-700">{error}</p>
      <button type="button" className="btn-primary mt-4" onClick={onRecalc}>
        Try again
      </button>
    </div>
  );
  if (!result) return <p className="text-sm text-asphalt/70">Press continue to calculate from your pricing engine.</p>;
  return <QuoteResultCard result={result} />;
}

function QuoteResultCard({ result }: { result: ProvisionalQuotation }) {
  const lines = result.breakdown?.lines?.filter((l) => typeof l.amount_gbp === "number") ?? [];
  return (
    <div className="text-center">
      <p className="text-sm text-asphalt/60">Provisional estimate (not saved yet)</p>
      <p className="mt-2 font-display text-4xl font-semibold text-asphalt">
        £{Number(result.total_inc_vat_gbp).toFixed(2)}
        <span className="text-base font-normal text-asphalt/60"> inc. VAT</span>
      </p>
      {result.subtotal_ex_vat_gbp != null && result.vat_gbp != null && (
        <p className="mt-1 text-xs text-asphalt/55">
          Ex VAT £{Number(result.subtotal_ex_vat_gbp).toFixed(2)} · VAT £{Number(result.vat_gbp).toFixed(2)}
        </p>
      )}
      {result.requires_approval && (
        <p className="mt-2 text-sm text-amber-800">This estimate requires owner verification before booking.</p>
      )}
      {lines.length > 0 && (
        <ul className="mx-auto mt-6 max-w-sm space-y-1 text-left text-sm text-asphalt/75">
          {lines.map((line) => (
            <li key={line.label} className="flex justify-between gap-4 border-b border-stone-line py-1">
              <span>{line.label}</span>
              {line.amount_gbp != null && <span>£{line.amount_gbp.toFixed(2)}</span>}
            </li>
          ))}
        </ul>
      )}
      <p className="mx-auto mt-6 max-w-md text-sm leading-relaxed text-asphalt/75">{result.provisional_disclaimer}</p>
    </div>
  );
}

function StepContact({
  state,
  patch,
  provisional,
  saved,
  submitting,
  error,
  onSubmit,
}: {
  state: QuoteState;
  patch: (p: Partial<QuoteState>) => void;
  provisional: ProvisionalQuotation | null;
  saved: SavedQuotation | null;
  submitting: boolean;
  error: string | null;
  onSubmit: () => void;
}) {
  const formValid =
    provisional &&
    state.full_name.trim().length >= 2 &&
    state.email.includes("@") &&
    state.address_line1.trim().length >= 3 &&
    state.consent_service_messages;

  return (
    <div>
      <h2 className="font-display text-xl font-semibold">Your details</h2>
      <p className="mt-2 text-sm text-asphalt/70">
        {provisional
          ? saved
            ? `Quotation ${saved.reference} saved. We will follow up using your contact details.`
            : "Save your estimate with genuine contact details — nothing is stored until you submit."
          : "Calculate your estimate on the previous step first."}
      </p>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <label className="text-sm">
          Full name
          <input
            required
            value={state.full_name}
            onChange={(e) => patch({ full_name: e.target.value })}
            className="mt-1 w-full rounded-md border px-3 py-2"
          />
        </label>
        <label className="text-sm">
          Email
          <input
            type="email"
            required
            value={state.email}
            onChange={(e) => patch({ email: e.target.value })}
            className="mt-1 w-full rounded-md border px-3 py-2"
          />
        </label>
        <label className="text-sm">
          Phone
          <input
            value={state.phone}
            onChange={(e) => patch({ phone: e.target.value })}
            className="mt-1 w-full rounded-md border px-3 py-2"
          />
        </label>
        <label className="text-sm md:col-span-2">
          Address line 1
          <input
            value={state.address_line1}
            onChange={(e) => patch({ address_line1: e.target.value })}
            className="mt-1 w-full rounded-md border px-3 py-2"
          />
        </label>
      </div>
      <label className="mt-4 flex items-start gap-2 text-sm">
        <input
          type="checkbox"
          checked={state.consent_service_messages}
          onChange={(e) => patch({ consent_service_messages: e.target.checked })}
        />
        <span>I agree to service messages about this quotation (required)</span>
      </label>
      <label className="mt-3 flex items-center gap-2 text-sm">
        <input type="checkbox" checked={state.consent_marketing} onChange={(e) => patch({ consent_marketing: e.target.checked })} />
        Email me occasional offers (optional)
      </label>
      {error && <p className="mt-4 text-sm text-red-700">{error}</p>}
      {provisional && !saved && (
        <button
          type="button"
          className="btn-primary mt-6"
          disabled={!formValid || submitting}
          onClick={onSubmit}
        >
          {submitting ? "Saving…" : "Save quotation & request follow-up"}
        </button>
      )}
      {!provisional && (
        <button type="button" className="btn-secondary mt-4" onClick={() => window.history.back()}>
          Back to estimate
        </button>
      )}
    </div>
  );
}