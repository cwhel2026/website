"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { MarketingCard } from "@/components/marketing-director-shell";
import { withLoadError } from "@/lib/load-errors";

export default function IntegrationsPage() {
  const [wizard, setWizard] = useState<Record<string, unknown> | null>(null);
  const [test, setTest] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Record<string, unknown>>("/api/v1/marketing/surfacecoat/meta/wizard", token).then(setWizard).catch(withLoadError(() => null));
  }, []);

  async function runTest() {
    const token = getToken();
    if (!token) return;
    const res = await apiPost<Record<string, unknown>>(
      "/api/v1/marketing/surfacecoat/meta/connection-test",
      {},
      token,
    );
    setTest(res);
  }

  const steps = (wizard?.steps as Array<{ id: string; title: string; env?: string[] }>) || [];
  const configured = (wizard?.configured as Record<string, boolean>) || {};

  return (
    <>
      <MarketingCard title="Meta connection wizard">
        <ul className="space-y-3 text-sm">
          {steps.map((s) => (
            <li key={s.id}>
              <p className="font-medium">{s.title}</p>
              {s.env?.map((e) => (
                <p key={e} className={configured[e] ? "text-emerald-700" : "text-slate-500"}>
                  {configured[e] ? "✓" : "○"} {e}
                </p>
              ))}
            </li>
          ))}
        </ul>
        <button
          type="button"
          onClick={runTest}
          className="mt-4 w-full rounded-full bg-[#eab308] py-2 text-sm font-semibold text-[#1a1a1a]"
        >
          Test connection
        </button>
        {test && (
          <pre className="mt-3 max-h-48 overflow-auto rounded bg-slate-100 p-2 text-xs">
            {JSON.stringify(test.tests || test, null, 2)}
          </pre>
        )}
      </MarketingCard>
    </>
  );
}