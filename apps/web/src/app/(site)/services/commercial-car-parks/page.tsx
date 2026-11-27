import Link from "next/link";
import { ServicePage } from "@/components/site/service-page";

export const metadata = {
  title: "Car park restoration and line marking",
  description: "Car park restoration and line marking. Quoted for the site, with no invented price and no confirmed booking.",
};

export default function Page() {
  return (
    <>
      <ServicePage
        slug="commercial-car-parks"
        title="Car park restoration and line marking"
        intro="Car park surfaces and line marking, scoped to the bays, access and condition we are asked to treat. There is no published price for this work yet."
        benefits={[
          "Restoration of suitable car park surfaces.",
          "Line marking quoted with the surface work, not as a guessed extra.",
          "A commercial enquiry records your details. It does not confirm a booking.",
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
