"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function HeroPostcode() {
  const router = useRouter();
  const [postcode, setPostcode] = useState("");

  function go(e: React.FormEvent) {
    e.preventDefault();
    const q = postcode.trim();
    if (!q) return;
    router.push(`/quote?postcode=${encodeURIComponent(q)}`);
  }

  return (
    <form onSubmit={go} className="mt-8 flex flex-col gap-2 sm:flex-row sm:items-stretch">
      <label className="sr-only" htmlFor="hero-postcode">
        Postcode
      </label>
      <input
        id="hero-postcode"
        value={postcode}
        onChange={(e) => setPostcode(e.target.value)}
        placeholder="Enter postcode"
        autoComplete="postal-code"
        className="min-w-0 flex-1 rounded-md border border-white/20 bg-white/10 px-4 py-3.5 text-white placeholder:text-white/50 backdrop-blur focus:border-restore-green focus:outline-none focus:ring-1 focus:ring-restore-green"
      />
      <button type="submit" className="btn-primary shrink-0 bg-white text-asphalt hover:bg-stone-wash">
        Check coverage & quote
      </button>
    </form>
  );
}