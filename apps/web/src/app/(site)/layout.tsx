import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { BusinessJsonLd } from "@/components/site/json-ld";
import { PrelaunchBanner } from "@/components/site/prelaunch-banner";
import { StickyQuote } from "@/components/site/sticky-quote";
import { SiteFrame } from "@/components/site/site-frame";

export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <SiteFrame>
      <BusinessJsonLd />
      <PrelaunchBanner />
      <SiteHeader />
      <main>{children}</main>
      <SiteFooter />
      <StickyQuote />
    </SiteFrame>
  );
}
