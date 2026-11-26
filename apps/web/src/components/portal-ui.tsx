import { brand } from "@/lib/brand";

export function PortalCard({
  title,
  children,
  className = "",
}: {
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-2xl border border-white/10 bg-white p-4 text-[#1a1a1a] shadow-sm ${className}`}>
      {title ? <h2 className="text-sm font-semibold text-[#1a1a1a]">{title}</h2> : null}
      <div className={title ? "mt-3 text-sm" : "text-sm"}>{children}</div>
    </section>
  );
}

export function PortalKpi({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="min-w-0 rounded-xl border border-white/10 bg-[#242424] p-3">
      <p className="text-[11px] font-medium uppercase tracking-wide text-white/55">{label}</p>
      <p className="mt-1 break-words text-lg font-semibold text-white">{value}</p>
      {hint ? <p className="mt-1 break-words text-xs text-white/50">{hint}</p> : null}
    </div>
  );
}

export function PortalPageTitle({
  title,
  subtitle,
}: {
  title: string;
  subtitle?: string;
}) {
  return (
    <header className="mb-5">
      <p className="text-[11px] font-semibold uppercase tracking-[0.2em]" style={{ color: brand.colors.gold }}>
        {brand.legalName}
      </p>
      <h1 className="mt-1 text-xl font-semibold text-white">{title}</h1>
      {subtitle ? <p className="mt-1 text-sm text-white/65">{subtitle}</p> : null}
    </header>
  );
}

export function PortalError({ message, detail }: { message: string; detail?: string }) {
  return (
    <div className="rounded-xl border border-red-400/30 bg-red-950/40 px-4 py-3 text-sm text-red-100" role="alert">
      <p className="font-medium">{message}</p>
      {detail ? <p className="mt-2 text-xs text-red-200/90">{detail}</p> : null}
    </div>
  );
}