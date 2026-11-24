export const metadata = { title: "Contact" };

export default function ContactPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-semibold text-emerald-950">Contact</h1>
      <p className="mt-4 text-emerald-900/80">
        For provisional quotations, use the{" "}
        <a href="/quote" className="font-semibold text-emerald-800 underline">
          instant quote
        </a>{" "}
        form. For general enquiries, email will be connected in Phase 3 — this page intentionally
        does not display unverified phone numbers or premises details.
      </p>
    </div>
  );
}