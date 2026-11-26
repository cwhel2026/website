/** SurfaceCoat Ltd — admin portal brand tokens (dashboard scope). */
export const brand = {
  legalName: "SurfaceCoat Ltd",
  portalTitle: "Business portal",
  tagline: "Operations, marketing & finance",
  colors: {
    charcoal: "#1a1a1a",
    charcoalElevated: "#242424",
    gold: "#eab308",
    goldMuted: "rgba(234, 179, 8, 0.15)",
    text: "#ffffff",
    textMuted: "rgba(255, 255, 255, 0.65)",
    textOnGold: "#1a1a1a",
    card: "#ffffff",
    cardBorder: "rgba(255, 255, 255, 0.12)",
    danger: "#f87171",
  },
} as const;

export const portalTheme = {
  page: "bg-[#1a1a1a] text-white min-h-screen overflow-x-hidden",
  header: "border-b border-white/10 bg-[#1a1a1a]/95 backdrop-blur supports-[backdrop-filter]:bg-[#1a1a1a]/80",
  card: "rounded-2xl border border-white/10 bg-white text-[#1a1a1a] shadow-sm",
  cardMuted: "rounded-2xl border border-white/10 bg-[#242424] text-white",
  btnPrimary:
    "inline-flex items-center justify-center rounded-full bg-[#eab308] px-4 py-2.5 text-sm font-semibold text-[#1a1a1a] transition hover:brightness-105 disabled:opacity-50",
  btnGhost:
    "inline-flex items-center justify-center rounded-full border border-white/20 px-4 py-2.5 text-sm font-medium text-white/90 hover:bg-white/5",
  linkActive: "bg-[#eab308] text-[#1a1a1a]",
  linkIdle: "text-white/80 hover:bg-white/10",
} as const;