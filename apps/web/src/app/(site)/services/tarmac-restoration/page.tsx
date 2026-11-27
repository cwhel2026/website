import { ServicePage } from "@/components/site/service-page";

export const metadata = {
  title: "Tarmac restoration",
  description: "Professional tarmac driveway restoration with an instant estimate and one customer total.",
};

export default function Page() {
  return (
    <ServicePage
      slug="tarmac-restoration"
      estimate="instant"
      title="Tarmac restoration"
      intro="Clean, prepare and coat faded tarmac when the existing driveway is suitable to keep. The online estimate shows one total."
      benefits={[
        "A published instant estimate from your measurements.",
        "Preparation and coating arranged as separate visits when washing is included.",
        "Repairs discussed separately and added only after you agree.",
      ]}
    />
  );
}
