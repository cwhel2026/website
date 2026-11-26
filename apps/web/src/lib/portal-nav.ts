import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  Bot,
  Building2,
  Calendar,
  Home,
  Megaphone,
  Menu,
  Settings,
  Users,
  Wallet,
  Wrench,
} from "lucide-react";

export type NavItem = { href: string; label: string; legacy?: boolean };

export type NavSection = {
  id: string;
  title: string;
  items: NavItem[];
};

/** Primary mobile bottom bar — secondary routes live in the drawer. */
export const BOTTOM_NAV: { href: string; label: string; icon: LucideIcon; matchPrefix?: string }[] = [
  { href: "/dashboard", label: "Home", icon: Home },
  { href: "/dashboard/calendar", label: "Diary", icon: Calendar },
  {
    href: "/dashboard/marketing/overview",
    label: "Marketing",
    icon: Megaphone,
    matchPrefix: "/dashboard/marketing",
  },
  {
    href: "/dashboard/finance-hub",
    label: "Money",
    icon: Wallet,
    matchPrefix: "/dashboard/finance-hub",
  },
  { href: "#more", label: "More", icon: Menu },
];

export const NAV_SECTIONS: NavSection[] = [
  {
    id: "overview",
    title: "Business overview",
    items: [
      { href: "/dashboard", label: "Home" },
      { href: "/dashboard/analytics", label: "Analytics" },
      { href: "/dashboard/system-health", label: "Integration health" },
      { href: "/dashboard/launch-readiness", label: "Launch readiness" },
    ],
  },
  {
    id: "assistant",
    title: "AI assistant",
    items: [
      { href: "/dashboard/assistant", label: "Assistant" },
      { href: "/dashboard/briefings", label: "Briefings" },
      { href: "/dashboard/automations", label: "Automations" },
      { href: "/dashboard/approvals", label: "Approvals" },
    ],
  },
  {
    id: "marketing",
    title: "Marketing",
    items: [
      { href: "/dashboard/marketing/overview", label: "Director overview" },
      { href: "/dashboard/marketing/campaigns", label: "Campaigns" },
      { href: "/dashboard/marketing/social-posts", label: "Social posts" },
      { href: "/dashboard/marketing/budget", label: "Budget & limits" },
      { href: "/dashboard/marketing/growth-fund", label: "Growth fund" },
      { href: "/dashboard/marketing/integrations", label: "Meta & integrations" },
      { href: "/dashboard/marketing-hub", label: "Marketing hub", legacy: true },
      { href: "/dashboard/content-studio", label: "Content studio", legacy: true },
    ],
  },
  {
    id: "sales",
    title: "Customers & sales",
    items: [
      { href: "/dashboard/customers", label: "Customers" },
      { href: "/dashboard/quotations", label: "Quotations" },
      { href: "/dashboard/commercial-leads", label: "Commercial leads" },
      { href: "/dashboard/flyers", label: "Flyers" },
    ],
  },
  {
    id: "ops",
    title: "Operations & scheduling",
    items: [
      { href: "/dashboard/calendar", label: "Diary" },
      { href: "/dashboard/jobs", label: "Jobs" },
      { href: "/dashboard/wash-pending", label: "Awaiting coating" },
      { href: "/dashboard/weather", label: "Weather" },
      { href: "/dashboard/territories", label: "Territories" },
      { href: "/dashboard/field", label: "Field (mobile)" },
      { href: "/dashboard/inventory", label: "Inventory" },
    ],
  },
  {
    id: "finance",
    title: "Accounting & finance",
    items: [
      { href: "/dashboard/finance-hub", label: "Money hub" },
      { href: "/dashboard/finance", label: "Finance" },
      { href: "/dashboard/invoices", label: "Invoices" },
      { href: "/dashboard/expenses", label: "Expenses" },
      { href: "/dashboard/tax-centre", label: "Tax & compliance" },
      { href: "/dashboard/director-pay", label: "Director pay" },
    ],
  },
  {
    id: "company",
    title: "Company & compliance",
    items: [
      { href: "/dashboard/company-setup", label: "Company setup" },
      { href: "/dashboard/website", label: "Website" },
    ],
  },
  {
    id: "settings",
    title: "Settings & integrations",
    items: [{ href: "/dashboard/system-health", label: "System health" }],
  },
];

export function isNavActive(pathname: string, href: string, matchPrefix?: string): boolean {
  if (href === "/dashboard") return pathname === "/dashboard";
  if (matchPrefix) return pathname === matchPrefix || pathname.startsWith(`${matchPrefix}/`);
  return pathname === href || pathname.startsWith(`${href}/`);
}

/** Compact icons for drawer section headers (optional). */
export const SECTION_ICONS: Record<string, LucideIcon> = {
  overview: BarChart3,
  assistant: Bot,
  marketing: Megaphone,
  sales: Users,
  ops: Wrench,
  finance: Wallet,
  company: Building2,
  settings: Settings,
};