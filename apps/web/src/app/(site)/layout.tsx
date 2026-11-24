import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { StickyQuote } from "@/components/site/sticky-quote";

export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-stone-wash pb-20 md:pb-0">
      <SiteHeader />
      <main>{children}</main>
      <SiteFooter />
      <StickyQuote />
    </div>
  );
}