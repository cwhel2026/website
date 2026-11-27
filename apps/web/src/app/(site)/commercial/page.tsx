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
    <div>
      <header className="bg-brand-ink text-white">
        <div className="site-container py-12 md:py-16">
          <p className="section-eyebrow text-brand-gold">Commercial</p>
          <h1 className="mt-3 font-display text-4xl font-medium md:text-5xl">Commercial surface restoration</h1>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/75">
            Car parks, forecourts and business yards. This form records an enquiry. It does not confirm a booking or
            show a price.
          </p>
        </div>
      </header>
      <div className="site-container py-12 md:py-16">
        <figure>
          <StockImage asset={MEDIA.services["commercial-car-parks"]} aspect="aspect-[21/9]" sizes="100vw" />
          <figcaption className="mt-2 text-xs text-brand-ink/60">
            {MEDIA.services["commercial-car-parks"].caption}
          </figcaption>
        </figure>

        {status === "ok" ? (
          <p className="mt-10 max-w-xl border border-brand-gold bg-white p-6 text-sm">
            Thank you. The enquiry was received. We will reply using the details you gave. This is not a confirmed booking.
          </p>
        ) : (
          <form onSubmit={onSubmit} className="mt-10 max-w-xl space-y-4 border border-brand-line bg-white p-6">
            <label className="block text-sm font-medium">
              Company name
              <input name="business_name" required className="mt-1 min-h-12 w-full border border-brand-line px-3" />
            </label>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="block text-sm font-medium">
                Email
                <input name="contact_email" type="email" required className="mt-1 min-h-12 w-full border border-brand-line px-3" />
              </label>
              <label className="block text-sm font-medium">
                Phone
                <input name="contact_phone" className="mt-1 min-h-12 w-full border border-brand-line px-3" />
              </label>
            </div>
            <label className="block text-sm font-medium">
              Site postcode
              <input name="postcode" className="mt-1 min-h-12 w-full border border-brand-line px-3" />
            </label>
            <label className="block text-sm font-medium">
              Site type
              <input name="category" placeholder="For example, retail park" className="mt-1 min-h-12 w-full border border-brand-line px-3" />
            </label>
            <label className="block text-sm font-medium">
              Project details
              <textarea name="notes" required rows={5} className="mt-1 w-full border border-brand-line px-3 py-3" />
            </label>
            <button type="submit" disabled={status === "loading"} className="btn-primary">
              {status === "loading" ? "Sending…" : "Submit commercial enquiry"}
            </button>
            {status === "err" ? <p className="text-sm text-red-700">Could not submit. Try again shortly.</p> : null}
          </form>
        )}

        <Link href="/quote" className="mt-8 inline-flex min-h-11 items-center text-sm font-semibold">
          Domestic instant estimate
        </Link>
      </div>
    </div>
  );
}
