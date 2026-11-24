export const metadata = { title: "Before and after gallery" };

export default function GalleryPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <h1 className="text-3xl font-semibold text-emerald-950">Before and after gallery</h1>
      <p className="mt-4 max-w-2xl text-emerald-900/80">
        Authentic project photography will be added as completed jobs are approved for marketing use.
        We do not display invented projects or stock images as customer work.
      </p>
      <div className="mt-10 grid gap-4 md:grid-cols-3">
        {[1, 2, 3].map((n) => (
          <div
            key={n}
            className="flex h-48 items-center justify-center rounded-xl border border-dashed border-emerald-300 bg-emerald-50/50 text-sm text-emerald-800/60"
          >
            Project slot {n} — awaiting approved imagery
          </div>
        ))}
      </div>
    </div>
  );
}