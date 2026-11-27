import { ServicePage } from "@/components/site/service-page";

export const metadata = {
  title: "Block paving restoration",
  description: "Block paving cleaning, re-sanding and sealing. A price is shown only when one has been confirmed.",
};

export default function Page() {
  return (
    <ServicePage
      slug="block-paving"
      title="Block paving restoration"
      intro="Cleaning, re-sanding and sealing for block paving where the blocks and the base are suitable to keep."
      benefits={[
        "Aimed at faded blocks, tired joints and surface grime.",
        "Not a replacement for a driveway whose base has failed.",
        "No published price until a rate is confirmed. No confirmed booking from this page.",
      ]}
    />
  );
}
