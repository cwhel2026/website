import { Suspense } from "react";
import { QuoteWizard } from "@/components/quote/quote-wizard";

export const metadata = {
  title: "Instant quotation",
  description: "Multi-step provisional driveway restoration quotation for North West England.",
};

export default function QuotePage() {
  return (
    <Suspense fallback={<p className="site-container py-20 text-asphalt/70">Loading quotation…</p>}>
      <QuoteWizard />
    </Suspense>
  );
}