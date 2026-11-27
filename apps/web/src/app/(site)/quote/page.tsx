import { Suspense } from "react";
import { QuoteWizard } from "@/components/quote/quote-wizard";

export const metadata = {
  title: "Instant quotation",
  description: "Instant driveway estimate. One total for tarmac restoration. Photographs are optional and do not delay the price.",
};

export default function QuotePage() {
  return (
    <Suspense fallback={<p className="site-container py-20 text-asphalt/70">Loading quotation…</p>}>
      <QuoteWizard />
    </Suspense>
  );
}