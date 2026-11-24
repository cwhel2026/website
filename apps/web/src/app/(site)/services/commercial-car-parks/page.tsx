import { ServicePage } from "@/components/site/service-page";
import Link from "next/link";

export const metadata = { title: "Commercial car park restoration" };

export default function Page() {
  return (
    <>
      <ServicePage
        slug="commercial-car-parks"
        title="Commercial car park restoration"
        intro="Large-area tarmac and surface restoration for retail, industrial and hospitality sites — sized and approved through your commercial workflow."
        benefits={[
          "Minimum job values and commercial multipliers from your configured pricing.",
          "Jobs requiring approval route to your approval centre.",
          "Dedicated commercial enquiry path for multi-site managers.",
        ]}
      />
      <p className="site-container -mt-8 pb-16">
        <Link href="/commercial" className="font-semibold text-restore-dark">
          Commercial enquiry form →
        </Link>
      </p>
    </>
  );
}