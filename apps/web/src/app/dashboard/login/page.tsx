"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiPost } from "@/lib/api";
import { mapLoginError } from "@/lib/api-errors";
import { setToken } from "@/lib/auth-client";

export default function DashboardLoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const form = new FormData(e.currentTarget);
    try {
      const data = await apiPost<{ access_token: string }>("/api/v1/auth/login", {
        email: String(form.get("email") || "").trim().toLowerCase(),
        password: form.get("password"),
      });
      setToken(data.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(mapLoginError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#1a1a1a] px-4 py-10 text-white">
      <div className="mx-auto w-full max-w-md">
        <LoginHeader />
        <form onSubmit={onSubmit} className="mt-8 rounded-2xl border border-white/10 bg-white p-6 shadow-xl text-[#1a1a1a]">
          <label className="block text-sm font-medium text-[#1a1a1a]">
            Email
            <input
              name="email"
              type="email"
              autoComplete="username"
              required
              className="mt-2 w-full rounded-lg border border-[#1a1a1a]/20 px-3 py-2.5 text-base focus:border-[#eab308] focus:outline-none focus:ring-2 focus:ring-[#eab308]/30"
            />
          </label>
          <label className="mt-4 block text-sm font-medium text-[#1a1a1a]">
            Password
            <div className="relative mt-2">
              <input
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                required
                className="w-full rounded-lg border border-[#1a1a1a]/20 px-3 py-2.5 pr-16 text-base focus:border-[#eab308] focus:outline-none focus:ring-2 focus:ring-[#eab308]/30"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 px-2 py-1 text-xs font-medium text-[#1a1a1a]/70"
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </label>
          {error && (
            <p className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800" role="alert">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="mt-6 flex w-full items-center justify-center gap-2 rounded-full bg-[#eab308] py-3 text-base font-semibold text-[#1a1a1a] disabled:opacity-60"
          >
            {loading && (
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-[#1a1a1a]/30 border-t-[#1a1a1a]" />
            )}
            {loading ? "Signing in…" : "Sign in"}
          </button>
          <p className="mt-4 text-center text-xs text-[#1a1a1a]/60">
            <Link href="/dashboard/login/recover" className="font-medium text-[#1a1a1a] underline">
              Forgot password?
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}

function LoginHeader() {
  return (
    <header className="text-center">
      <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[#eab308]">SurfaceCoat</p>
      <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white">Business portal</h1>
      <p className="mt-2 text-sm text-white/70">SurfaceCoat Ltd — authorised staff only</p>
    </header>
  );
}