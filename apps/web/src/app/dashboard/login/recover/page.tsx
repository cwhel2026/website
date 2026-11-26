"use client";

import Link from "next/link";
import { useState } from "react";
import { apiPost } from "@/lib/api";
import { mapLoginError } from "@/lib/api-errors";

export default function PasswordRecoverPage() {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);
    const form = new FormData(e.currentTarget);
    try {
      const res = await apiPost<{ message: string }>("/api/v1/auth/owner/recover", {
        setup_key: form.get("setup_key"),
        new_password: form.get("new_password"),
      });
      setMessage(res.message);
    } catch (err) {
      setError(mapLoginError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#1a1a1a] px-4 py-10 text-white">
      <div className="mx-auto w-full max-w-md">
        <h1 className="text-center text-xl font-semibold">Password recovery</h1>
        <p className="mt-2 text-center text-sm text-white/70">
          Use the secure setup key from your operator. If you do not have one, contact your system administrator.
        </p>
        <form onSubmit={onSubmit} className="mt-8 rounded-2xl border border-white/10 bg-white p-6 text-[#1a1a1a]">
          <label className="block text-sm font-medium">
            Setup key
            <input
              name="setup_key"
              type="password"
              required
              autoComplete="off"
              className="mt-2 w-full rounded-lg border px-3 py-2.5"
            />
          </label>
          <label className="mt-4 block text-sm font-medium">
            New password
            <input
              name="new_password"
              type="password"
              required
              minLength={12}
              autoComplete="new-password"
              className="mt-2 w-full rounded-lg border px-3 py-2.5"
            />
          </label>
          {error && <p className="mt-4 text-sm text-red-700">{error}</p>}
          {message && <p className="mt-4 text-sm text-emerald-800">{message}</p>}
          <button
            type="submit"
            disabled={loading}
            className="mt-6 w-full rounded-full bg-[#eab308] py-3 font-semibold text-[#1a1a1a] disabled:opacity-60"
          >
            {loading ? "Updating…" : "Update password"}
          </button>
          <p className="mt-4 text-center text-xs">
            <Link href="/dashboard/login" className="underline">
              Back to sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}