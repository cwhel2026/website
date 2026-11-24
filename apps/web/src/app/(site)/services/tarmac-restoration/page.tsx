import { ServicePage } from "@/components/site/service-page";

export const metadata = {
  title: "Tarmac restoration",
  description: "Professional tarmac driveway restoration and protective coatings across the North West.",
};

export default function Page() {
  return (
    <ServicePage
      slug="tarmac-restoration"
      title="Tarmac restoration"
      intro="Revive faded and weathered tarmac with structured preparation and specialist restoration coatings — where the existing surface is suitable."
      benefits={[
        "Refresh kerb appeal without replacing sound hardstanding.",
        "Two-visit wash and coat workflow when washing is required.",
        "Pricing from your live regional engine — provisional online, verified on site.",
      ]}
    />
  );
}