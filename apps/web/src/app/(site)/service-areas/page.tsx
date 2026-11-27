import { CoverageChecker } from "@/components/home/coverage-checker";
import { publicBrand } from "@/lib/public-brand";

export const metadata = {
  title: "Areas we cover",
  description: `Surface restoration across ${publicBrand.coverageAreas}.`,
};

export default function ServiceAreasPage() {
  return (
    <div>
      <header className="bg-brand-ink text-white">
        <div className="site-container py-12 md:py-16">
          <p className="section-eyebrow text-brand-gold">Areas we cover</p>
          <h1 className="mt-3 max-w-3xl font-display text-4xl font-medium leading-tight md:text-5xl">
            {publicBrand.coverageAreas}.
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/75">
            The postcode check uses our live coverage. Local pages explain the work in a town. They are not a claim
            that we have a depot there.
          </p>
        </div>
      </header>
      <div className="site-container py-12 md:py-16">
        <CoverageChecker />
      </div>
    </div>
  );
}
