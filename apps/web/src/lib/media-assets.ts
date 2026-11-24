/**
 * Public-site imagery — verified UK Geograph reference photos (CC BY-SA 2.0).
 * Paths point at committed WebP/AVIF under /public/media/approved/.
 * Illustrative before/after uses the same reference frame; the "after" side is a licensed derivative treatment.
 */

export type MediaAsset = {
  id: string;
  src: string;
  srcWebp: string;
  srcAvif?: string;
  alt: string;
  kind: "reference" | "owned_project" | "override" | "illustrative_derivative";
  credit: string;
  license: string;
  sourceUrl?: string;
  caption?: string;
};

const approved = (basename: string) => ({
  webp: `/media/approved/${basename}.webp`,
  avif: `/media/approved/${basename}.avif`,
});

function asset(
  id: string,
  basename: string,
  alt: string,
  credit: string,
  sourceUrl: string,
  kind: MediaAsset["kind"],
  caption?: string,
): MediaAsset {
  const paths = approved(basename);
  return {
    id,
    src: paths.webp,
    srcWebp: paths.webp,
    srcAvif: paths.avif,
    alt,
    kind,
    credit,
    license: "CC BY-SA 2.0 (Geograph Britain and Ireland)",
    sourceUrl,
    caption,
  };
}

/** Services with no verified UK imprinted-concrete reference on file — UI shows a pending placeholder. */
export const PENDING_SERVICE_IMAGES = ["imprinted-concrete"] as const;

export const MEDIA = {
  hero: asset(
    "hero-home",
    "hero-home",
    "UK residential tarmac driveway leading to a rural property",
    "Phil Catterall / Geograph 409433",
    "https://www.geograph.org.uk/photo/409433",
    "reference",
    "Licensed reference photo — not a completed Revive My Drive project.",
  ),
  beforeAfter: {
    before: asset(
      "before-shoreham",
      "ba-before",
      "Cracked residential tarmac driveway in the UK (before)",
      "Simon Carey / Geograph 276811",
      "https://www.geograph.org.uk/photo/276811",
      "reference",
    ),
    after: asset(
      "after-shoreham-illustrative",
      "ba-after",
      "Same driveway — illustrative colour refresh (digital treatment on reference photo)",
      "Derivative of Simon Carey / Geograph 276811",
      "https://www.geograph.org.uk/photo/276811",
      "illustrative_derivative",
    ),
    caption:
      "Illustrative comparison using one UK reference photograph. The “after” side is a colour/contrast treatment on the same frame — not a real Revive My Drive job. Authentic project pairs will replace this when approved.",
  },
  services: {
    "tarmac-restoration": asset(
      "tarmac-service",
      "tarmac-surface",
      "Worn UK tarmac driveway surface",
      "Phil Catterall / Geograph 409433",
      "https://www.geograph.org.uk/photo/409433",
      "reference",
    ),
    "block-paving": asset(
      "block-paving",
      "block-paving",
      "UK block-paved residential driveway",
      "Robin Stott / Geograph 4239736",
      "https://www.geograph.org.uk/photo/4239736",
      "reference",
    ),
    "minor-repairs": asset(
      "minor-repairs",
      "tarmac-wear",
      "UK tarmac driveway with localised wear and vegetation",
      "Maigheach-gheal / Geograph 2435499",
      "https://www.geograph.org.uk/photo/2435499",
      "reference",
    ),
    "commercial-car-parks": asset(
      "commercial",
      "commercial-lot",
      "UK tarmac access road and commercial-style hardstanding",
      "Snowmanradio / Geograph (Hearsall Common)",
      "https://www.geograph.org.uk/photo/610171",
      "reference",
    ),
  } satisfies Record<string, MediaAsset>,
} as const;

export function serviceMedia(slug: string): MediaAsset | undefined {
  if ((PENDING_SERVICE_IMAGES as readonly string[]).includes(slug)) {
    return undefined;
  }
  return MEDIA.services[slug as keyof typeof MEDIA.services];
}