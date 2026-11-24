export const metadata = { title: "Project gallery" };

export default function GalleryPage() {
  return (
    <div className="site-container py-16 md:py-24">
      <p className="section-eyebrow">Gallery</p>
      <h1 className="mt-2 font-display text-4xl font-semibold text-asphalt">Authentic project photography</h1>
      <p className="mt-4 max-w-2xl text-asphalt/75">
        This gallery intentionally stays empty until verified before-and-after photographs are approved for
        publication. We do not present stock or generated images as completed work.
      </p>
      <p className="mt-8 rounded-lg border border-dashed border-stone-line bg-white p-12 text-center text-sm text-asphalt/55">
        No published projects yet — add approved media via the website management area when available.
      </p>
    </div>
  );
}