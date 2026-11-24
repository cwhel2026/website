import { ServicePage } from "@/components/site/service-page";

export const metadata = { title: "Minor surface repairs" };

export default function Page() {
  return (
    <ServicePage
      slug="minor-repairs"
      title="Minor surface repairs"
      intro="Targeted repairs alongside wider restoration programmes — scoped once we understand the defect, not every driveway."
      benefits={[
        "Localized defect treatment where compatible with restoration coatings.",
        "Honest scoping when replacement of failed areas is more appropriate.",
        "Quoted after measurements and condition assessment.",
      ]}
    />
  );
}