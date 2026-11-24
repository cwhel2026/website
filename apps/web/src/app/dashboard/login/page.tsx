"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiPost } from "@/lib/api";
import { setToken } from "@/lib/auth-client";

export default function DashboardLoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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
          Default dev credentials are set via API environment variables (see README).
        </p>
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