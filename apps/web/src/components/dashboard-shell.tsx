"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth-client";

const nav = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/assistant", label: "AI Assistant" },
  { href: "/dashboard/approvals", label: "Approvals" },
  { href: "/dashboard/briefings", label: "Briefings" },
  { href: "/dashboard/automations", label: "Automations" },
  { href: "/dashboard/marketing/overview", label: "Marketing director" },
  { href: "/dashboard/marketing-hub", label: "Marketing hub (legacy)" },
  { href: "/dashboard/launch-readiness", label: "Launch readiness" },
  { href: "/dashboard/content-studio", label: "Content studio (legacy)" },
  { href: "/dashboard/website", label: "Website" },
  { href: "/dashboard/commercial-leads", label: "Commercial leads" },
  { href: "/dashboard/flyers", label: "Flyers" },
  { href: "/dashboard/company-setup", label: "Company setup" },
  { href: "/dashboard/finance-hub", label: "Money hub" },
  { href: "/dashboard/tax-centre", label: "Tax & compliance" },
  { href: "/dashboard/director-pay", label: "Director pay" },
  { href: "/dashboard/finance", label: "Finance" },
  { href: "/dashboard/invoices", label: "Invoices" },
  { href: "/dashboard/expenses", label: "Expenses" },
  { href: "/dashboard/analytics", label: "Analytics" },
  { href: "/dashboard/inventory", label: "Inventory" },
  { href: "/dashboard/system-health", label: "System health" },
  { href: "/dashboard/calendar", label: "Calendar" },
  { href: "/dashboard/jobs", label: "Jobs" },
  { href: "/dashboard/wash-pending", label: "Awaiting coating" },
  { href: "/dashboard/weather", label: "Weather" },
  { href: "/dashboard/territories", label: "Territories" },
  { href: "/dashboard/customers", label: "Customers" },
  { href: "/dashboard/quotations", label: "Quotations" },
  { href: "/dashboard/field", label: "Field (mobile)" },
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (pathname === "/dashboard/login") {
      setReady(true);
      return;
    }
    const token = getToken();
    if (!token) {
      router.replace("/dashboard/login");
      return;
    }
    apiGet("/api/v1/auth/me", token)
      .then(() => setReady(true))
      .catch(() => {
        clearToken();
        router.replace("/dashboard/login");
      });
  }, [pathname, router]);

  if (pathname === "/dashboard/login") return <>{children}</>;
  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center text-emerald-900">
        Loading business dashboard…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div>
            <p className="font-semibold text-emerald-950">Revive My Drive — Control Centre</p>
            <p className="text-xs text-slate-500">Phase 1 foundation (live data when API connected)</p>
          </div>
          <button
            type="button"
            className="text-sm text-slate-600"
            onClick={() => {
              clearToken();
              router.push("/dashboard/login");
            }}
          >
            Sign out
          </button>
        </div>
      </header>
      <div className="mx-auto grid max-w-6xl gap-6 px-4 py-6 md:grid-cols-[200px_1fr]">
        <nav className="space-y-1 text-sm">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-lg px-3 py-2 ${
                pathname === item.href ? "bg-emerald-900 text-white" : "text-slate-700 hover:bg-white"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="min-h-[60vh] rounded-xl border bg-white p-6 shadow-sm">{children}</div>
      </div>
    </div>
  );
}