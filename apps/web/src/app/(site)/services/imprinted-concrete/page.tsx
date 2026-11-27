import { ServicePage } from "@/components/site/service-page";

export const metadata = {
  title: "Pattern-imprinted concrete restoration",
  description: "Pattern-imprinted concrete restoration. A price is shown only when one has been confirmed.",
};

export default function Page() {
  return (
    <ServicePage
      slug="imprinted-concrete"
      title="Pattern-imprinted concrete restoration"
      intro="Colour and protection for pattern-imprinted concrete, after preparation suited to the sealer already on the surface."
      benefits={[
        "For faded pattern-imprinted concrete that is still sound.",
        "Preparation depends on the existing coating. We do not promise every sealer can be overcoated.",
        "No published price until a rate is confirmed. No confirmed booking from this page.",
      ]}
    />
  );
}
