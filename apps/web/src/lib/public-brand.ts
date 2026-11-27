/** Customer-facing website (not the admin portal). */
export const publicBrand = {
  tradingName: "SurfaceCoat",
  legalName: "SurfaceCoat Ltd",
  tagline: "Restore. Protect. Transform.",
  /** Shown on marketing pages. Preston is an internal travel base and is not advertised as a premises. */
  coverageAreas:
    "Lancashire, Greater Manchester, Merseyside, Cheshire, Cumbria, West Yorkshire and surrounding areas",
  counties: [
    "Lancashire",
    "Greater Manchester",
    "Merseyside",
    "Cheshire",
    "Cumbria",
    "West Yorkshire",
  ],
  launchLabel: "March 2027",
} as const;

/** Pre-launch is on unless NEXT_PUBLIC_PRELAUNCH is false or 0. */
export function prelaunchMode(): boolean {
  const flag = process.env.NEXT_PUBLIC_PRELAUNCH;
  return flag !== "false" && flag !== "0";
}
