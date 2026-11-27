"use client";

import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPut } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { withLoadError } from "@/lib/load-errors";

type Task = {
  slug: string;
  title: string;
  plain_language: string;
  status: string;
  due_date?: string | null;
};

type Summary = {
  completion_pct: number;
  next_actions: string[];
  profile: {
    registered_name?: string | null;
    companies_house_number?: string | null;
    incorporation_date?: string | null;
    trading_start_date?: string | null;
    registered_office?: string | null;
    company_utr?: string | null;
    vat_status: string;
    vat_number?: string | null;
    vat_rate_percent?: string | number | null;
    vat_effective_from?: string | null;
    paye_status: string;
    corporation_tax_registered?: boolean | null;
    accountant_name?: string | null;
    accountant_email?: string | null;
    tasks: Task[];
  };
};

export default function CompanySetupPage() {
  const [data, setData] = useState<Summary | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Summary>("/api/v1/company/profile", token)
      .then((s) => {
        setData(s);
        setForm({
          registered_name: s.profile.registered_name ?? "SurfaceCoat Ltd",
          companies_house_number: s.profile.companies_house_number ?? "",
          incorporation_date: s.profile.incorporation_date ?? "",
          trading_start_date: s.profile.trading_start_date ?? "",
          registered_office: s.profile.registered_office ?? "",
          company_utr: s.profile.company_utr ?? "",
          accountant_name: s.profile.accountant_name ?? "",
          accountant_email: s.profile.accountant_email ?? "",
          vat_status: s.profile.vat_status ?? "not_registered",
          vat_number: s.profile.vat_number ?? "",
          vat_rate_percent: s.profile.vat_rate_percent != null ? String(s.profile.vat_rate_percent) : "20",
          vat_effective_from: s.profile.vat_effective_from ?? "",
        });
      })
      .catch(withLoadError(() => setData(null)));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function save() {
    const token = getToken();
    if (!token) return;
    setSaving(true);
    setMsg(null);
    try {
      const body: Record<string, unknown> = { ...form };
      if (!body.companies_house_number) body.companies_house_number = null;
      if (!body.incorporation_date) {
        body.incorporation_date = null;
      }
      if (!body.trading_start_date) {
        body.trading_start_date = null;
      }
      if (!body.vat_effective_from) body.vat_effective_from = null;
      if (!body.vat_number) body.vat_number = null;
      if (body.vat_rate_percent) body.vat_rate_percent = Number(body.vat_rate_percent);
      if (form.corporation_tax_registered === "true") {
        body.corporation_tax_registered = true;
      } else if (form.corporation_tax_registered === "false") {
        body.corporation_tax_registered = false;
      }
      await apiPut("/api/v1/company/profile", body, token);
      setMsg("Saved — checklist deadlines updated from your company details.");
      load();
    } catch {
      setMsg("Save failed — is the API running with migration 0004 applied?");
    } finally {
      setSaving(false);
    }
  }

  if (!data) {
    return (
      <div>
        <h1 className="text-2xl font-semibold text-emerald-950">Company setup</h1>
        <p className="mt-2 text-sm text-slate-600">Loading…</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-semibold text-emerald-950">UK limited company setup</h1>
      <p className="mt-2 text-sm text-slate-600">
        SurfaceCoat Ltd operates as a private limited company. Complete these details so deadlines and tax guidance use
        real information — nothing is assumed about incorporation or HMRC registration.
      </p>

      <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-950">
        Onboarding progress: <strong>{data.completion_pct}%</strong>
        {data.next_actions.length > 0 ? (
          <ul className="mt-2 list-disc pl-5">
            {data.next_actions.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        ) : null}
      </div>

      <section className="mt-6 space-y-3 rounded-lg border bg-white p-4 text-sm">
        <h2 className="font-semibold text-slate-900">Company details</h2>
        {(
          [
            ["registered_name", "Registered name"],
            ["companies_house_number", "Companies House number"],
            ["incorporation_date", "Incorporation date (YYYY-MM-DD)"],
            ["trading_start_date", "Trading start date"],
            ["registered_office", "Registered office"],
            ["company_utr", "Company UTR (when HMRC issues it)"],
            ["accountant_name", "Accountant name"],
            ["accountant_email", "Accountant email"],
          ] as const
        ).map(([key, label]) => (
          <label key={key} className="block">
            <span className="text-slate-700">{label}</span>
            <input
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              value={form[key] ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
            />
          </label>
        ))}
        <label className="block">
          <span className="text-slate-700">Registered for corporation tax with HMRC?</span>
          <select
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            value={form.corporation_tax_registered ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, corporation_tax_registered: e.target.value }))}
          >
            <option value="">Not sure yet</option>
            <option value="true">Yes</option>
            <option value="false">Not yet</option>
          </select>
        </label>
        <h2 className="pt-2 font-semibold text-slate-900">VAT registration</h2>
        <p className="text-slate-600">
          SurfaceCoat is not VAT registered. Estimates and invoices exclude VAT until you record a registration and the
          date it takes effect. Quotes already issued keep the tax treatment they were given.
        </p>
        <label className="block">
          <span className="text-slate-700">VAT status</span>
          <select
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            value={form.vat_status ?? "not_registered"}
            onChange={(e) => setForm((f) => ({ ...f, vat_status: e.target.value }))}
          >
            <option value="not_registered">Not registered</option>
            <option value="applied">Applied, not yet registered</option>
            <option value="registered">Registered</option>
          </select>
        </label>
        <label className="block">
          <span className="text-slate-700">VAT number</span>
          <input
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            value={form.vat_number ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, vat_number: e.target.value }))}
          />
        </label>
        <label className="block">
          <span className="text-slate-700">VAT rate (%)</span>
          <input
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            value={form.vat_rate_percent ?? "20"}
            onChange={(e) => setForm((f) => ({ ...f, vat_rate_percent: e.target.value }))}
          />
        </label>
        <label className="block">
          <span className="text-slate-700">Effective from (YYYY-MM-DD)</span>
          <input
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            value={form.vat_effective_from ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, vat_effective_from: e.target.value }))}
          />
        </label>
        <button
          type="button"
          disabled={saving}
          onClick={save}
          className="rounded bg-emerald-700 px-4 py-2 text-white disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save company profile"}
        </button>
        {msg ? <p className="text-slate-600">{msg}</p> : null}
      </section>

      <section className="mt-8">
        <h2 className="font-semibold text-slate-900">Checklist</h2>
        <ul className="mt-3 space-y-3">
          {data.profile.tasks.map((t) => (
            <li key={t.slug} className="rounded-lg border border-slate-200 bg-white p-4 text-sm">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="font-medium text-slate-900">{t.title}</span>
                <span className="text-xs uppercase tracking-wide text-slate-500">{t.status.replace(/_/g, " ")}</span>
              </div>
              <p className="mt-2 text-slate-600">{t.plain_language}</p>
              {t.due_date ? (
                <p className="mt-1 text-xs text-amber-800">Suggested deadline: {t.due_date}</p>
              ) : null}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}