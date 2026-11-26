"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PortalPageTitle } from "@/components/portal-ui";

const TABS = [
  { href: "/dashboard/marketing/overview", label: "Overview" },
  { href: "/dashboard/marketing/social-posts", label: "Social" },
  { href: "/dashboard/marketing/campaigns", label: "Campaigns" },
  { href: "/dashboard/marketing/leads", label: "Leads" },
  { href: "/dashboard/marketing/creative-intelligence", label: "Creative" },
  { href: "/dashboard/marketing/geo", label: "Geo" },
  { href: "/dashboard/marketing/budget", label: "Budget" },
  { href: "/dashboard/marketing/growth-fund", label: "Growth fund" },
  { href: "/dashboard/marketing/recommendations", label: "AI" },
  { href: "/dashboard/marketing/integrations", label: "Integrations" },
] as const;

export function MarketingDirectorShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="-mx-4 -mt-4 md:-mx-6 md:-mt-6">
      <PortalPageTitle
        title="Marketing director"
        subtitle="Facebook & Instagram · Preston · pre-launch safe"
      />
      <nav
        className="mb-4 flex max-w-full gap-2 overflow-x-auto pb-1 text-xs [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        aria-label="Marketing sections"
      >
        {TABS.map((t) => {
          const active = pathname === t.href || pathname.startsWith(`${t.href}/`);
          return (
            <Link
              key={t.href}
              href={t.href}
              className={`shrink-0 whitespace-nowrap rounded-full px-3 py-2 min-h-[40px] flex items-center ${
                active ? "bg-[#eab308] font-semibold text-[#1a1a1a]" : "border border-white/15 bg-white/5 text-white/90"
              }`}
            >
              {t.label}
            </Link>
          );
        })}
      </nav>
      <div className="max-w-full overflow-x-hidden">{children}</div>
    </div>
  );
}

export function MarketingCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mb-4 rounded-2xl border border-white/10 bg-white p-4 text-[#1a1a1a]">
      <h2 className="text-sm font-semibold text-[#1a1a1a]">{title}</h2>
      <div className="mt-3 text-sm">{children}</div>
    </section>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <p className="rounded-xl border border-white/15 bg-white/5 px-3 py-4 text-center text-sm text-white/75">
      {message}
    </p>
  );
}