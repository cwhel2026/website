import type { Metadata } from "next";
import { DashboardShell } from "@/components/dashboard-shell";
import { brand } from "@/lib/brand";

export const metadata: Metadata = {
  title: { absolute: `${brand.legalName} — ${brand.portalTitle}` },
  robots: { index: false, follow: false },
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <DashboardShell>{children}</DashboardShell>;
}
