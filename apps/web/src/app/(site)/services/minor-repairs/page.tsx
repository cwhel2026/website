import { ServicePage } from "@/components/site/service-page";

export const metadata = {
  title: "Surface repairs",
  description: "Surface repairs agreed and priced separately from the restoration estimate.",
};

export default function Page() {
  return (
    <ServicePage
      slug="minor-repairs"
      title="Surface repairs"
      intro="Local repairs that may sit alongside restoration. They are looked at, priced and agreed before they are added. Minor edge wear is not an automatic charge."
      benefits={[
        "Close-up photographs help us see cracks and damaged areas.",
        "A photograph does not confirm the structure and does not change the restoration total.",
        "If a repair is not the right answer, we say so before any work is agreed.",
      ]}
    />
  );
}
