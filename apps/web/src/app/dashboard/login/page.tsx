"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { apiPost } from "@/lib/api";
import { setToken } from "@/lib/auth-client";

export default function DashboardLoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [hint, setHint] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    Promise.all([fetch("/api/ops/status"), fetch("/api/deploy-hint")])
      .then(async ([opsRes, hintRes]) => {
        const ops = await opsRes.json();
        const hintData = await hintRes.json();
        if (ops.combined_sidecar && ops.api?.reachable) return;
        setHint(
          ops.api?.reason ??
            hintData.fix_when_login_fails ??
            "FastAPI is not running. Clear Railway Root directory (repo root) and redeploy — RAILWAY_LOGIN_FIX.md.",
        );
      })
      .catch(() => setHint(null));
  }, []);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const form = new FormData(e.currentTarget);
    try {
      const data = await apiPost<{ access_token: string }>("/api/v1/auth/login", {
        email: form.get("email"),
        password: form.get("password"),
      });
      setToken(data.access_token);
      router.push("/dashboard");
    } catch {
      setError("Login failed. Ensure the API is running and credentials are correct.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <form onSubmit={onSubmit} className="w-full max-w-md rounded-2xl border bg-white p-8 shadow-sm">
        <h1 className="text-xl font-semibold text-emerald-950">Business sign in</h1>
        <p className="mt-2 text-sm text-slate-600">
          Sign in with <strong>DEFAULT_ADMIN_EMAIL</strong> and <strong>DEFAULT_ADMIN_PASSWORD</strong> from Railway
          (API service or combined website service).
        </p>
        {hint && (
          <div className="mt-3 space-y-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
            <p>{hint}</p>
            <p className="font-semibold">Railway fix (keep variables on website):</p>
            <ol className="list-decimal pl-4">
              <li>Settings → Build → Dockerfile path: <code className="text-[11px]">Dockerfile</code> (repo root)</li>
              <li>Settings → Deploy → Custom start: <code className="text-[11px]">/app/start.sh</code></li>
              <li>Health check path: <code className="text-[11px]">/health</code></li>
              <li>Redeploy, then sign in with DEFAULT_ADMIN_EMAIL / DEFAULT_ADMIN_PASSWORD</li>
            </ol>
          </div>
        )}
        <label className="mt-6 block text-sm">
          Email
          <input name="email" type="email" required className="mt-1 w-full rounded-lg border px-3 py-2" />
        </label>
        <label className="mt-4 block text-sm">
          Password
          <input name="password" type="password" required className="mt-1 w-full rounded-lg border px-3 py-2" />
        </label>
        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="mt-6 w-full rounded-full bg-emerald-900 py-3 font-semibold text-white"
        >
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}