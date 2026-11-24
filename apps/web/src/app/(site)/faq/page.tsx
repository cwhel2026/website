const faqs = [
  {
    q: "Are online quotes final?",
    a: "No. Online quotes are provisional. We confirm measurements, surface condition, access and product suitability on site before booking.",
  },
  {
    q: "Why two visits for restoration?",
    a: "Most restorations need pressure washing first and a protective coating once the surface is dry. We target coating within seven days where product and weather allow.",
  },
  {
    q: "Which areas do you cover?",
    a: "We operate across North West England territories listed on the Service areas page. Minimum charges and travel vary by region.",
  },
];

export const metadata = { title: "FAQ" };

export default function FaqPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-semibold text-emerald-950">Frequently asked questions</h1>
      <dl className="mt-8 space-y-6">
        {faqs.map((item) => (
          <div key={item.q}>
            <dt className="font-semibold text-emerald-950">{item.q}</dt>
            <dd className="mt-2 text-emerald-900/80">{item.a}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}