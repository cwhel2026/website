import { ServicePage } from "@/components/site/service-page";

export const metadata = { title: "Block paving restoration" };

export default function Page() {
  return (
    <ServicePage
      slug="block-paving"
      title="Block paving restoration"
      intro="Cleaning, re-sanding and sealing for block paved driveways where the installation is fundamentally sound."
      benefits={[
        "Restore colour contrast between blocks without replacing the entire driveway.",
        "Address weeds and jointing as part of a structured restoration plan.",
        "Suitable for many residential drives — verified before booking.",
      ]}
    />
  );
}