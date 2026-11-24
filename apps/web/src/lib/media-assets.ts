/**
 * Configurable public-site imagery. Paths point at committed stock files or dashboard overrides.
 * Stock assets are illustrative only — never presented as completed Revive My Drive projects.
 */

export type MediaAsset = {
  id: string;
  src: string;
  alt: string;
  /** stock | owned_project | override */
  kind: "stock" | "owned_project" | "override";
  credit?: string;
  caption?: string;
};

const STOCK = (path: string) => path;

export const MEDIA = {
  hero: {
    id: "hero-home",
    src: STOCK("/media/stock/hero-home.jpg"),
    alt: "Residential property with driveway — stock illustration",
    kind: "stock" as const,
    credit: "Unsplash (stock)",
    caption: "Stock atmosphere photography — not a completed Revive My Drive project.",
  },
  beforeAfter: {
    before: {
      id: "before-tarmac",
      src: STOCK("/media/stock/tarmac-worn.jpg"),
      alt: "Worn tarmac driveway — stock illustration (before)",
      kind: "stock" as const,
      credit: "Unsplash (stock)",
    },
    after: {
      id: "after-driveway",
      src: STOCK("/media/stock/driveway-refreshed.jpg"),
      alt: "Refreshed residential driveway — stock illustration (after)",
      kind: "stock" as const,
      credit: "Unsplash (stock)",
    },
    caption:
      "Illustrative stock comparison only — not a verified before/after from a Revive My Drive job. Authentic project pairs will replace this when approved.",
  },
  services: {
    "tarmac-restoration": {
      id: "tarmac-service",
      src: STOCK("/media/stock/tarmac-worn.jpg"),
      alt: "Tarmac driveway — stock illustration",
      kind: "stock" as const,
      credit: "Unsplash (stock)",
    },
    "block-paving": {
      id: "block-paving",
      src: STOCK("/media/stock/block-paving.jpg"),
      alt: "Block paving — stock illustration",
      kind: "stock" as const,
      credit: "Unsplash (stock)",
    },
    "imprinted-concrete": {
      id: "imprinted",
      src: STOCK("/media/stock/pattern-concrete.jpg"),
      alt: "Patterned concrete — stock illustration",
      kind: "stock" as const,
      credit: "Unsplash (stock)",
    },
    "minor-repairs": {
      id: "repairs",
      src: STOCK("/media/stock/tarmac-worn.jpg"),
      alt: "Surface wear — stock illustration",
      kind: "stock" as const,
      credit: "Unsplash (stock)",
    },
    "commercial-car-parks": {
      id: "commercial",
      src: STOCK("/media/stock/commercial-lot.jpg"),
      alt: "Commercial property — stock illustration",
      kind: "stock" as const,
      credit: "Unsplash (stock)",
    },
  } satisfies Record<string, MediaAsset>,
} as const;

export function serviceMedia(slug: string): MediaAsset | undefined {
  return MEDIA.services[slug as keyof typeof MEDIA.services];
}