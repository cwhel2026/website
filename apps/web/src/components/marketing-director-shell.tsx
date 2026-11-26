"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/dashboard/marketing/overview", label: "Overview" },
  { href: "/dashboard/marketing/social-posts", label: "Social posts" },
  { href: "/dashboard/marketing/campaigns", label: "Campaigns" },
  { href: "/dashboard/marketing/leads", label: "Leads" },
  { href: "/dashboard/marketing/creative-intelligence", label: "Creative intelligence" },
  { href: "/dashboard/marketing/geo", label: "Geo" },
  { href: "/dashboard/marketing/budget", label: "Budget" },
  { href: "/dashboard/marketing/growth-fund", label: "Growth fund" },
  { href: "/dashboard/marketing/recommendations", label: "AI recommendations" },
  { href: "/dashboard/marketing/integrations", label: "Integrations" },
] as const;

export function MarketingDirectorShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="min-h-screen bg-[#1a1a1a] text-white">
      <header className="border-b border-white/10 px-4 py-4">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#eab308]">SurfaceCoat</p>
        <h1 className="text-xl font-semibold">Marketing director</h1>
        <p className="mt-1 text-sm text-white/70">Facebook & Instagram · Preston · pre-launch safe</p>
      </header>
      <nav className="flex gap-2 overflow-x-auto border-b border-white/10 px-2 py-2 text-xs">
        {TABS.map((t) => {
          const active = pathname === t.href || pathname.startsWith(`${t.href}/`);
          return (
            <Link
              key={t.href}
              href={t.href}
              className={`whitespace-nowrap rounded-full px-3 py-1.5 ${
                active ? "bg-[#eab308] text-[#1a1a1a] font-semibold" : "bg-white/10 text-white/90"
              }`}
            >
              {t.label}
            </Link>
          );
        })}
      </nav>
      <main className="mx-auto max-w-lg px-4 py-6">{children}</main>
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
    <section className="mb-6 rounded-2xl border border-white/10 bg-white p-4 text-[#1a1a1a]">
      <h2 className="text-sm font-semibold text-[#1a1a1a]">{title}</h2>
      <div className="mt-3 text-sm">{children}</div>
    </section>
  );
}

export function EmptyState({ message }: { message: string }) {
  return <p className="rounded-lg bg-slate-100 px-3 py-4 text-center text-slate-600">{message}</p>;
}