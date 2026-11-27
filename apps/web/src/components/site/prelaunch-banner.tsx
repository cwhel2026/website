import { prelaunchMode, publicBrand } from "@/lib/public-brand";

export function PrelaunchBanner() {
  if (!prelaunchMode()) return null;
  return (
    <p className="bg-brand-charcoal px-4 py-2 text-center text-xs leading-relaxed text-white/85">
      Launching {publicBrand.launchLabel}. Estimates are open. A request is not a confirmed visit.
    </p>
  );
}
