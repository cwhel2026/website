import Link from "next/link";
import { ServicePage } from "@/components/site/service-page";

export const metadata = {
  title: "Commercial surface restoration",
  description: "Commercial surface restoration for yards, forecourts and business hardstanding. No invented price.",
};

export default function Page() {
  return (
    <>
      <ServicePage
        slug="commercial-restoration"
        title="Commercial surface restoration"
        intro="Forecourts, yards and other business hardstanding. The work is quoted for the site. We do not publish a price until one is confirmed."
        benefits={[
          "For commercial surfaces that are suitable to restore rather than replace.",
          "Access, area and condition are agreed before any visit is confirmed.",
          "An enquiry is not a booking and is not a price.",
        ]}
      />
      <p className="site-container -mt-6 pb-16">
        <Link href="/commercial" className="text-sm font-semibold underline-offset-4 hover:underline">
          Send a commercial enquiry
        </Link>
      </p>
    </>
  );
}
