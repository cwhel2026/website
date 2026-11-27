import Link from "next/link";
import { TransformationGallery } from "@/components/site/transformation-gallery";

export const metadata = {
  title: "Transformations",
  description:
    "Illustrative before-and-after comparisons. These are not completed SurfaceCoat projects until genuine photographs are published.",
};

export default function TransformationsPage() {
  return (
    <div>
      <header className="bg-brand-ink text-white">
        <div className="site-container py-12 md:py-16">
          <p className="section-eyebrow text-brand-gold">Transformations</p>
          <h1 className="mt-3 max-w-3xl font-display text-4xl font-medium leading-tight md:text-5xl">
            Illustrative, until the work is ours.
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/75">
            Comparisons use one licensed photograph and the same camera position. The refreshed side is a treatment
            of that photograph. It is not a finished SurfaceCoat driveway.
          </p>
        </div>
      </header>
      <div className="site-container py-12 md:py-16">
        <TransformationGallery />
        <Link href="/quote" className="btn-primary mt-10">
          Get my instant estimate
        </Link>
      </div>
    </div>
  );
}
