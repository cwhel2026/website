"use client";

import { useState } from "react";
import Link from "next/link";
import { StockImage } from "@/components/site/stock-image";
import { apiPost } from "@/lib/api";
import { MEDIA } from "@/lib/media-assets";

export default function CommercialPage() {
  const [status, setStatus] = useState<"idle" | "loading" | "ok" | "err">("idle");

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus("loading");
    const fd = new FormData(e.currentTarget);
    try {
      await apiPost("/api/v1/public/commercial-enquiry", {
        business_name: String(fd.get("business_name")),
        contact_email: String(fd.get("contact_email")),
        contact_phone: String(fd.get("contact_phone") || "") || null,
        address_line1: String(fd.get("address_line1") || "") || null,
        town: String(fd.get("town") || "") || null,
        postcode: String(fd.get("postcode") || "") || null,
        category: String(fd.get("category") || "") || null,
        notes: String(fd.get("notes")),
      });
      setStatus("ok");
      e.currentTarget.reset();
    } catch {
      setStatus("err");
    }
  }

  return (
    <div className="site-container py-16 md:py-24">
      <p className="section-eyebrow">Commercial restoration</p>
      <h1 className="mt-2 font-display text-4xl font-semibold text-asphalt">Partner with Revive My Drive</h1>
      <p className="mt-4 max-w-2xl text-lg leading-relaxed text-asphalt/75">
        Car parks, forecourts, retail parks, industrial estates, hotels and managing agents — surface
        restoration and maintenance enquiries routed to your commercial CRM pipeline.
      </p>

      <div className="mt-8 overflow-hidden rounded-lg border border-stone-line shadow-sm">
        <StockImage asset={MEDIA.services["commercial-car-parks"]} aspect="aspect-[21/9]" sizes="100vw" />
        <p className="border-t border-stone-line bg-stone-wash px-4 py-2 text-xs text-asphalt/60">
          Licensed UK reference photo — not a completed Revive My Drive commercial project.
        </p>
      </div>

      <ul className="mt-8 grid gap-3 sm:grid-cols-2 text-sm text-asphalt/80">
        {["Car park re-colouring", "Forecourt restoration", "Scheduled cleaning", "Targeted repairs"].map((i) => (
          <li key={i} className="border-l-2 border-restore-green pl-3">
            {i}
          </li>
        ))}
      </ul>

      {status === "ok" ? (
        <p className="mt-10 rounded-lg border border-restore-green/40 bg-restore-muted/50 p-6 text-restore-dark">
          Thank you — your enquiry was received. We will respond using the contact details provided.
        </p>
      ) : (
        <form onSubmit={onSubmit} className="mt-10 max-w-xl space-y-4 rounded-lg border border-stone-line bg-white p-8">
          <label className="block text-sm font-medium">
            Company name
            <input name="business_name" required className="mt-1 w-full rounded-md border px-3 py-2" />
          </label>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block text-sm font-medium">
              Email
              <input name="contact_email" type="email" required className="mt-1 w-full rounded-md border px-3 py-2" />
            </label>
            <label className="block text-sm font-medium">
              Phone
              <input name="contact_phone" className="mt-1 w-full rounded-md border px-3 py-2" />
            </label>
          </div>
          <label className="block text-sm font-medium">
            Site postcode
            <input name="postcode" className="mt-1 w-full rounded-md border px-3 py-2" />
          </label>
          <label className="block text-sm font-medium">
            Site type
            <input name="category" placeholder="e.g. retail park" className="mt-1 w-full rounded-md border px-3 py-2" />
          </label>
          <label className="block text-sm font-medium">
            Project details (area, services, access restrictions)
            <textarea name="notes" required rows={5} className="mt-1 w-full rounded-md border px-3 py-2" />
          </label>
          <button type="submit" disabled={status === "loading"} className="btn-primary">
            {status === "loading" ? "Sending…" : "Submit commercial enquiry"}
          </button>
          {status === "err" && <p className="text-sm text-red-700">Could not submit — try again shortly.</p>}
        </form>
      )}

      <Link href="/quote" className="mt-8 inline-block text-sm font-semibold text-restore-dark">
        Domestic instant quote →
      </Link>
    </div>
  );
}