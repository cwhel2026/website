export function SimulatedBadge({ label = "SIMULATED — not running, no spend" }: { label?: string }) {
  return (
    <span className="ml-2 inline-block rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-900">
      {label}
    </span>
  );
}
