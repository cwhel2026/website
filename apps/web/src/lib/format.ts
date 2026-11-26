/** GBP for display. Missing values are "Unknown", never £0.00 or NaN. */
export function gbp(value: unknown, unknown = "Unknown"): string {
  if (value === null || value === undefined || value === "") return unknown;
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n)) return unknown;
  return `£${n.toLocaleString("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function pct(numerator: unknown, denominator: unknown): string {
  const a = Number(numerator);
  const b = Number(denominator);
  if (!Number.isFinite(a) || !Number.isFinite(b) || b === 0) return "—";
  return `${((a / b) * 100).toFixed(1)}%`;
}
