import { ServicePage } from "@/components/site/service-page";

export const metadata = { title: "Imprinted concrete restoration" };

export default function Page() {
  return (
    <ServicePage
      slug="imprinted-concrete"
      title="Imprinted concrete restoration"
      intro="Refresh pattern-imprinted concrete with appropriate cleaning, preparation and colour revival treatments."
      benefits={[
        "Improve appearance of stamped concrete that has faded over time.",
        "Preparation matched to existing sealer or coating condition.",
        "Provisional pricing via the same regional engine as tarmac services.",
      ]}
    />
  );
}