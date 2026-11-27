"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ApiError } from "@/lib/api";
import { apiDelete, apiGet, apiPost, resolveApiUrl } from "@/lib/api";
import { trackFunnel, getStoredUtm } from "@/lib/analytics";

const STORAGE_KEY = "rmd_quote_draft";
const STEPS = ["Location", "Surface", "Measurements", "Condition", "Preparation", "Photos", "Quote", "Contact"];

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
  intention: "" | "ready_to_book" | "callback_requested" | "estimate_requested";
  callback_preferred_time: string;
  photoToken: string;
  photoNote: string;
};

type LocalPhoto = { id: string; url: string };

type PackageItem = { title: string; detail: string };

type ProvisionalQuotation = {
  input_fingerprint: string;
  total_gbp: string | number | null;
  vat_applied: boolean;
  customer_note: string;
  repairs_note: string;
  included: PackageItem[];
  visits: PackageItem[];
  surface_supported: boolean;
  unsupported_reason?: string | null;
  total_area_sqm?: string | number | null;
};

type SuggestedWindow = { label: string; starts: string; kind: string };

type SavedQuotation = {
  reference: string;
  total_gbp: string | number;
  vat_applied: boolean;
  intention: string;
  appointment_confirmed: boolean;
  email_sent: boolean;
  email_status: string;
  next_steps: string;
  suggested_windows: SuggestedWindow[];
  photo_later_path?: string;
  photos_attached?: boolean;
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
    intention: "",
    callback_preferred_time: "",
    photoToken: "",
    photoNote: "",
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
  const [photos, setPhotos] = useState<LocalPhoto[]>([]);
  const [uploading, setUploading] = useState(false);

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
    sessionStorage.removeItem(IDEMPOTENCY_KEY);
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
      if (data.total_gbp == null) {
        setError("Unable to calculate a price for these inputs.");
        return;
      }
      setProvisional(data);
      void trackFunnel("quote_estimate", 5);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(
          err.status >= 500
            ? "We could not calculate a price right now. Your details are still saved — try again shortly."
            : err.message,
        );
      } else {
        setError("Quotation could not be calculated. Your details are still saved.");
      }
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
      full_name: state.full_name.trim(),
      email: state.email.trim(),
      phone: state.phone?.trim() || null,
      address_line1: state.address_line1.trim(),
      address_line2: state.address_line2?.trim() || null,
      visible_damage: state.visible_damage || null,
      consent_service_messages: true,
      consent_marketing: state.consent_marketing,
      intention: state.intention || "estimate_requested",
      callback_preferred_time: state.callback_preferred_time.trim() || null,
      input_fingerprint: provisional.input_fingerprint,
      idempotency_key: idempotencyKey,
      source: utm.source ?? "website",
      campaign: utm.campaign ?? null,
      photo_token: state.photoToken || null,
      photo_note: state.photoNote.trim() || null,
    };
    try {
      const data = await apiPost<SavedQuotation>("/api/v1/quotations/submit", payload);
      setSaved(data);
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
    if (step === 6 && !provisional) void calculateProvisional();
    else setStep((s) => Math.min(s + 1, STEPS.length - 1));
  }

  function back() {
    setStep((s) => Math.max(s - 1, 0));
  }

  function chooseAction(intention: QuoteState["intention"]) {
    patch({ intention });
    setError(null);
    setStep(7);
  }

  async function showEstimate() {
    setError(null);
    setStep(6);
    await calculateProvisional();
  }

  async function uploadFiles(fileList: FileList | null, replaceId?: string) {
    if (!fileList || fileList.length === 0) return;
    setUploading(true);
    setError(null);
    try {
      const form = new FormData();
      if (state.photoToken) form.append("token", state.photoToken);
      if (state.photoNote.trim()) form.append("note", state.photoNote.trim());
      if (replaceId) form.append("replace_id", replaceId);
      for (const file of Array.from(fileList)) {
        form.append("files", await compressPhoto(file), "driveway.jpg");
      }
      const res = await fetch(`${resolveApiUrl()}/api/v1/quotation-photos`, {
        method: "POST",
        body: form,
        credentials: "same-origin",
      });
      if (!res.ok) {
        const detail = await res.text();
        let message = "Could not upload the photograph";
        try {
          const parsed = JSON.parse(detail) as { detail?: string };
          if (typeof parsed.detail === "string") message = parsed.detail;
        } catch {
          if (detail) message = detail;
        }
        throw new Error(message);
      }
      const data = (await res.json()) as { token: string; photos: { id: string }[] };
      patch({ photoToken: data.token });
      setPhotos(
        data.photos.map((photo) => ({
          id: photo.id,
          url: `/api/v1/quotation-photos/${data.token}/${photo.id}`,
        })),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not upload the photograph");
    } finally {
      setUploading(false);
    }
  }

  async function removePhoto(photoId: string) {
    if (!state.photoToken) return;
    setError(null);
    try {
      const data = await apiDelete<{ photos: { id: string }[] }>(
        `/api/v1/quotation-photos/${state.photoToken}/${photoId}`,
      );
      setPhotos(
        data.photos.map((photo) => ({
          id: photo.id,
          url: `/api/v1/quotation-photos/${state.photoToken}/${photo.id}`,
        })),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove the photograph");
    }
  }

  return (
    <div className="min-h-screen bg-stone-wash pb-24">
      <div className="site-container py-10 md:py-14">
        <p className="section-eyebrow">Instant quotation</p>
        <h1 className="mt-2 font-display text-3xl font-semibold text-asphalt md:text-4xl">
          Your provisional price in minutes
        </h1>

        <ol
          className="mt-8 grid grid-cols-4 gap-2 text-[10px] sm:grid-cols-8 sm:text-xs"
          aria-label="Progress"
        >
          {STEPS.map((label, i) => (
            <li
              key={label}
              className={`rounded-full px-2 py-1.5 text-center leading-tight ${
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
            <StepPhotos
              note={state.photoNote}
              photos={photos}
              uploading={uploading}
              error={error}
              onNote={(photoNote) => patch({ photoNote })}
              onUpload={(files, replaceId) => void uploadFiles(files, replaceId)}
              onRemove={(photoId) => void removePhoto(photoId)}
              onSkip={() => void showEstimate()}
              onEstimate={() => void showEstimate()}
            />
          )}
          {step === 6 && (
            <StepQuote
              result={provisional}
              loading={loading}
              error={error}
              onRecalc={() => void calculateProvisional()}
              onChoose={chooseAction}
            />
          )}
          {step === 7 && (
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
            {step < 7 && step !== 5 && !(step === 6 && provisional) && (
              <button
                type="button"
                onClick={next}
                disabled={step === 0 && !state.postcode.trim()}
                className="btn-primary"
              >
                {step === 6 ? "Calculate estimate" : "Continue"}
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
      <p className="mt-2 text-sm text-asphalt/70">Enter the property postcode so we can check we cover the area.</p>
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

async function compressPhoto(file: File): Promise<Blob> {
  try {
    const bitmap = await createImageBitmap(file);
    const scale = Math.min(1, 1600 / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(bitmap.width * scale));
    canvas.height = Math.max(1, Math.round(bitmap.height * scale));
    const context = canvas.getContext("2d");
    if (!context) return file;
    context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.8));
    return blob ?? file;
  } catch {
    return file;
  }
}

function StepPhotos({
  note,
  photos,
  uploading,
  error,
  onNote,
  onUpload,
  onRemove,
  onSkip,
  onEstimate,
}: {
  note: string;
  photos: LocalPhoto[];
  uploading: boolean;
  error: string | null;
  onNote: (value: string) => void;
  onUpload: (files: FileList | null, replaceId?: string) => void;
  onRemove: (photoId: string) => void;
  onSkip: () => void;
  onEstimate: () => void;
}) {
  const [open, setOpen] = useState(photos.length > 0);
  const replaceRef = useRef<string | null>(null);
  return (
    <div className="text-[#1a1a1a]">
      <h2 className="font-display text-xl font-semibold">Photographs</h2>
      <p className="mt-3 text-sm leading-relaxed text-[#1a1a1a]/80">
        If you have any cracks or areas that may need repairing, please include a close-up photograph. Minor wear
        around edges is perfectly normal.
      </p>
      <div className="mt-6 flex flex-col gap-3">
        <button
          type="button"
          className="w-full rounded-md border border-[#1a1a1a] bg-white px-6 py-4 text-base font-semibold"
          onClick={() => setOpen(true)}
        >
          Upload driveway photos
        </button>
        <button
          type="button"
          className="w-full rounded-md bg-[#e0b323] px-6 py-4 text-base font-semibold text-[#1a1a1a]"
          onClick={onSkip}
        >
          I just want an estimate
        </button>
      </div>
      {open && (
        <div className="mt-6">
          <div className="flex flex-col gap-3 sm:flex-row">
            <label className="w-full rounded-md border border-[#1a1a1a] px-4 py-3 text-center text-sm font-semibold">
              Take a photo
              <input
                type="file"
                accept="image/*"
                capture="environment"
                className="sr-only"
                data-testid="camera-input"
                onChange={(event) => onUpload(event.target.files)}
              />
            </label>
            <label className="w-full rounded-md border border-[#1a1a1a] px-4 py-3 text-center text-sm font-semibold">
              Choose from gallery
              <input
                type="file"
                accept="image/*"
                multiple
                className="sr-only"
                data-testid="gallery-input"
                onChange={(event) => {
                  const replacing = replaceRef.current ?? undefined;
                  replaceRef.current = null;
                  onUpload(event.target.files, replacing);
                  event.target.value = "";
                }}
              />
            </label>
          </div>
          {photos.length > 0 && (
            <ul className="mt-4 grid grid-cols-2 gap-3">
              {photos.map((photo) => (
                <li key={photo.id} className="rounded-md border border-stone-line p-2">
                  <img src={photo.url} alt="Driveway photograph" className="h-28 w-full rounded object-cover" />
                  <div className="mt-2 flex gap-2">
                    <button type="button" className="text-sm underline" onClick={() => onRemove(photo.id)}>
                      Remove photograph
                    </button>
                    <button
                      type="button"
                      className="text-sm underline"
                      onClick={() => {
                        replaceRef.current = photo.id;
                        document.querySelector<HTMLInputElement>("[data-testid=gallery-input]")?.click();
                      }}
                    >
                      Replace photograph
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
          <label className="mt-4 block text-sm font-medium">
            Notes (optional)
            <textarea
              value={note}
              onChange={(event) => onNote(event.target.value)}
              rows={3}
              className="mt-1 w-full rounded-md border border-stone-line px-4 py-3"
            />
          </label>
          <button
            type="button"
            className="mt-4 w-full rounded-md bg-[#e0b323] px-6 py-4 text-base font-semibold text-[#1a1a1a] disabled:opacity-50"
            disabled={uploading}
            onClick={onEstimate}
          >
            {uploading ? "Uploading…" : "See my estimate"}
          </button>
        </div>
      )}
      {error && <p className="mt-4 text-sm text-red-700">{error}</p>}
    </div>
  );
}

function StepQuote({
  result,
  loading,
  error,
  onRecalc,
  onChoose,
}: {
  result: ProvisionalQuotation | null;
  loading: boolean;
  error: string | null;
  onRecalc: () => void;
  onChoose: (intention: QuoteState["intention"]) => void;
}) {
  if (loading) return <p className="text-center py-12 text-asphalt/70">Calculating your estimate…</p>;
  if (error) return (
    <div>
      <p className="text-sm text-red-700">{error}</p>
      <button type="button" className="btn-primary mt-4" onClick={onRecalc}>
        Try again
      </button>
    </div>
  );
  if (!result) return <p className="text-sm text-asphalt/70">Press Calculate estimate to see your price.</p>;
  return <QuoteResultCard result={result} onChoose={onChoose} />;
}

function QuoteResultCard({
  result,
  onChoose,
}: {
  result: ProvisionalQuotation;
  onChoose: (intention: QuoteState["intention"]) => void;
}) {
  return (
    <div className="text-center text-[#1a1a1a]">
      <p className="text-sm tracking-wide text-[#1a1a1a]/70">Your estimated price</p>
      <p className="mt-2 font-display text-4xl font-semibold">
        £{Number(result.total_gbp).toFixed(2)}
        {result.vat_applied ? (
          <span className="text-base font-normal text-[#1a1a1a]/60"> including VAT</span>
        ) : null}
      </p>
      <div className="mx-auto mt-6 h-1 w-16 rounded-full bg-[#e0b323]" />
      <ul className="mx-auto mt-6 max-w-md space-y-3 text-left text-sm">
        {result.included.map((item) => (
          <li key={item.title}>
            <p className="font-semibold">{item.title}</p>
            <p className="text-[#1a1a1a]/70">{item.detail}</p>
          </li>
        ))}
      </ul>
      <ul className="mx-auto mt-6 max-w-md space-y-3 text-left text-sm">
        {result.visits.map((item) => (
          <li key={item.title} className="rounded-md border border-[#e0b323]/50 bg-white px-3 py-2">
            <p className="font-semibold">{item.title}</p>
            <p className="text-[#1a1a1a]/70">{item.detail}</p>
          </li>
        ))}
      </ul>
      <p className="mx-auto mt-6 max-w-md text-sm leading-relaxed text-[#1a1a1a]/75">{result.repairs_note}</p>
      <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-[#1a1a1a]/75">{result.customer_note}</p>
      <div className="mx-auto mt-8 flex max-w-md flex-col gap-3 text-left">
        <button
          type="button"
          onClick={() => onChoose("ready_to_book")}
          className="w-full rounded-md bg-[#e0b323] px-6 py-4 text-base font-semibold text-[#1a1a1a] hover:brightness-95"
        >
          Book me in ASAP
        </button>
        <button
          type="button"
          onClick={() => onChoose("callback_requested")}
          className="w-full rounded-md border border-[#1a1a1a] bg-white px-6 py-4 text-base font-semibold text-[#1a1a1a]"
        >
          Request a callback
        </button>
        <button
          type="button"
          onClick={() => onChoose("estimate_requested")}
          className="w-full rounded-md border border-[#1a1a1a] bg-white px-6 py-4 text-base font-semibold text-[#1a1a1a]"
        >
          Email me my estimate
        </button>
      </div>
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
  const needsPhone = state.intention === "ready_to_book" || state.intention === "callback_requested";
  const phoneDigits = state.phone.replace(/\D/g, "");
  const formValid =
    provisional &&
    state.full_name.trim().length >= 2 &&
    state.email.includes("@") &&
    state.address_line1.trim().length >= 3 &&
    (!needsPhone || phoneDigits.length >= 8) &&
    (state.intention !== "callback_requested" || state.callback_preferred_time.trim().length >= 2);

  if (saved) {
    return (
      <div>
        <h2 className="font-display text-xl font-semibold text-[#1a1a1a]">What happens next</h2>
        <p className="mt-4 text-sm leading-relaxed text-[#1a1a1a]/80">{saved.next_steps}</p>
        <p className="mt-4 text-sm font-semibold text-[#1a1a1a]">
          Reference {saved.reference} · £{Number(saved.total_gbp).toFixed(2)}
          {saved.vat_applied ? " including VAT" : ""}
        </p>
        {saved.suggested_windows.length > 0 && (
          <ul className="mt-4 space-y-2 text-sm">
            {saved.suggested_windows.map((window) => (
              <li key={`${window.kind}-${window.starts}`} className="rounded-md border border-[#e0b323]/60 px-3 py-2">
                <p className="font-semibold">{window.label}</p>
                <p className="text-[#1a1a1a]/70">
                  {new Date(window.starts).toLocaleString("en-GB", { timeZone: "Europe/London" })}. Nothing is reserved.
                </p>
              </li>
            ))}
          </ul>
        )}
        {saved.appointment_confirmed === false && (
          <p className="mt-4 text-sm text-[#1a1a1a]/75">Your appointment is not confirmed yet.</p>
        )}
        {saved.photo_later_path && (
          <p className="mt-4 text-sm">
            <a href={saved.photo_later_path} className="underline">
              Add or update photographs
            </a>
          </p>
        )}
      </div>
    );
  }

  const title =
    state.intention === "ready_to_book"
      ? "Book the earliest visit"
      : state.intention === "callback_requested"
        ? "Request a callback"
        : "Email me my estimate";
  const submitLabel =
    state.intention === "ready_to_book"
      ? "Book me in ASAP"
      : state.intention === "callback_requested"
        ? "Request my callback"
        : "Email my estimate";

  return (
    <div>
      <h2 className="font-display text-xl font-semibold text-[#1a1a1a]">{title}</h2>
      <p className="mt-3 rounded-md bg-stone-wash px-3 py-2 text-sm text-[#1a1a1a]/80">
        {[state.address_line1, state.town, state.postcode].filter(Boolean).join(", ") || state.postcode}
      </p>
      <div className="mt-6 grid gap-4">
        <label className="text-sm font-medium">
          Your name
          <input
            required
            autoComplete="name"
            value={state.full_name}
            onChange={(e) => patch({ full_name: e.target.value })}
            className="mt-1 w-full rounded-md border border-stone-line px-4 py-3"
          />
        </label>
        <label className="text-sm font-medium">
          Email
          <input
            type="email"
            required
            autoComplete="email"
            value={state.email}
            onChange={(e) => patch({ email: e.target.value })}
            className="mt-1 w-full rounded-md border border-stone-line px-4 py-3"
          />
        </label>
        {needsPhone && (
          <label className="text-sm font-medium">
            Telephone
            <input
              required
              type="tel"
              autoComplete="tel"
              value={state.phone}
              onChange={(e) => patch({ phone: e.target.value })}
              className="mt-1 w-full rounded-md border border-stone-line px-4 py-3"
            />
          </label>
        )}
        {state.intention === "callback_requested" && (
          <label className="text-sm font-medium">
            Best time to call
            <input
              required
              value={state.callback_preferred_time}
              onChange={(e) => patch({ callback_preferred_time: e.target.value })}
              placeholder="Weekday mornings"
              className="mt-1 w-full rounded-md border border-stone-line px-4 py-3"
            />
          </label>
        )}
        <label className="text-sm font-medium">
          Property address
          <input
            required
            autoComplete="street-address"
            value={state.address_line1}
            onChange={(e) => patch({ address_line1: e.target.value })}
            className="mt-1 w-full rounded-md border border-stone-line px-4 py-3"
          />
        </label>
      </div>
      <p className="mt-4 text-sm text-[#1a1a1a]/75">
        We use these details to respond to this request.{" "}
        <a href="/privacy" className="underline">
          Privacy notice
        </a>
      </p>
      <label className="mt-3 flex items-start gap-2 text-sm text-[#1a1a1a]/80">
        <input
          type="checkbox"
          className="mt-1"
          checked={state.consent_marketing}
          onChange={(e) => patch({ consent_marketing: e.target.checked })}
        />
        Send me occasional news from SurfaceCoat. This is optional.
      </label>
      {error && <p className="mt-4 text-sm text-red-700">{error}</p>}
      {provisional && (
        <button
          type="button"
          className={
            state.intention === "ready_to_book"
              ? "mt-6 w-full rounded-md bg-[#e0b323] px-6 py-4 text-base font-semibold text-[#1a1a1a] disabled:opacity-50"
              : "btn-primary mt-6 w-full disabled:opacity-50"
          }
          disabled={!formValid || submitting}
          onClick={onSubmit}
        >
          {submitting ? "Sending…" : submitLabel}
        </button>
      )}
    </div>
  );
}