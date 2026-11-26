"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
import { withLoadError } from "@/lib/load-errors";

type Centre = {
  integrations: Array<{
    platform: string;
    state: string;
    railway_env_vars: string[];
    setup_steps: string;
    live_read_verified?: boolean;
    live_write_verified?: boolean;
  }>;
};

export default function MarketingIntegrationsPage() {
  const [data, setData] = useState<Centre | null>(null);
  const [testResult, setTestResult] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    apiGet<Centre>("/api/v1/marketing/integrations/setup-centre", token).then(setData).catch(withLoadError(() => setData(null)));
  }, []);

  const testMeta = async () => {
    const token = getToken();
    if (!token) return;
    const r = await apiPost<Record<string, unknown>>("/api/v1/marketing/integrations/test/meta-insights", {}, token);
    setTestResult(JSON.stringify(r));
  };

  return (
    <div className="max-w-2xl space-y-4 pb-16">
      <h1 className="text-2xl font-semibold text-emerald-950">Integration setup centre</h1>
      <p className="text-sm text-slate-600">Secrets live in Railway — tests never expose values.</p>
      <button type="button" onClick={testMeta} className="rounded bg-slate-800 px-3 py-2 text-sm text-white">
        Test Meta insights
      </button>
      {testResult && <pre className="overflow-x-auto rounded border p-2 text-xs">{testResult}</pre>}
      <ul className="space-y-3">
        {(data?.integrations || []).map((i) => (
          <li key={i.platform} className="rounded-lg border p-3 text-sm">
            <p className="font-semibold">{i.platform}</p>
            <p className="text-slate-600">State: {i.state}</p>
            {i.railway_env_vars?.length > 0 && (
              <p className="text-xs text-slate-500">Env: {i.railway_env_vars.join(", ")}</p>
            )}
            <p className="mt-1 text-slate-700">{i.setup_steps}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}