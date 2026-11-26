import { MarketingDirectorShell } from "@/components/marketing-director-shell";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return <MarketingDirectorShell>{children}</MarketingDirectorShell>;
}