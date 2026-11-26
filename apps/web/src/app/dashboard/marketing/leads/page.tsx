"use client";

import Link from "next/link";
import { MarketingCard } from "@/components/marketing-director-shell";

export default function LeadsPage() {
  return (
    <MarketingCard title="Leads & conversions">
      <p className="text-sm text-slate-600">
        Meta instant forms and website enquiries flow into CRM with attribution. Configure webhooks in Integrations.
      </p>
      <Link href="/dashboard/customers" className="mt-3 inline-block text-sm font-medium underline">
        View customers & enquiries
      </Link>
    </MarketingCard>
  );
}