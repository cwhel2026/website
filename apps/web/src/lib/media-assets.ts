/**
 * Public-site photographs. Each before/after pair is the same surface,
 * supplied for the service it shows. Captions name the service only.
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

function photo(id: string, basename: string, alt: string, caption?: string): MediaAsset {
  const paths = approved(basename);
  return {
    id,
    src: paths.webp,
    srcWebp: paths.webp,
    srcAvif: paths.avif,
    alt,
    kind: "override",
    credit: "",
    license: "",
    caption,
  };
}

/** No service is waiting on a photograph. */
export const PENDING_SERVICE_IMAGES = [] as const;

const tarmacApproachAfter = photo(
  "tarmac-approach-after",
  "tarmac-approach-after",
  "Restored black tarmac driveway in front of a house",
  "Tarmac restoration",
);

const carParkAfter = photo(
  "car-park-after",
  "car-park-after",
  "Restored black tarmac car park in front of a brick office",
  "Tarmac restoration on a car park",
);

export const MEDIA = {
  hero: tarmacApproachAfter,
  services: {
    "tarmac-restoration": tarmacApproachAfter,
    "block-paving": photo(
      "block-seal-after",
      "block-seal-after",
      "Block paving after a wash and wet-look seal",
      "Block paving after a wash and wet-look seal",
    ),
    "imprinted-concrete": photo(
      "imprinted-drive-after",
      "imprinted-drive-after",
      "Restored pattern-imprinted concrete driveway",
      "Pattern-imprinted concrete restoration",
    ),
    "minor-repairs": photo(
      "tarmac-drive-before",
      "tarmac-drive-before",
      "Worn tarmac driveway before restoration",
      "Worn tarmac before restoration",
    ),
    "commercial-car-parks": carParkAfter,
    "commercial-restoration": carParkAfter,
  } satisfies Record<string, MediaAsset>,
} as const;

export type RestorationPair = {
  id: string;
  title: string;
  before: MediaAsset;
  after: MediaAsset;
  caption: string;
};

export const RESTORATION_PAIRS: RestorationPair[] = [
  {
    id: "tarmac-drive",
    title: "Tarmac driveway",
    before: photo("tarmac-drive-before", "tarmac-drive-before", "Tarmac driveway before restoration"),
    after: photo("tarmac-drive-after", "tarmac-drive-after", "Tarmac driveway after restoration"),
    caption: "Tarmac restoration. The same driveway, before and after.",
  },
  {
    id: "imprinted-patio",
    title: "Patterned concrete",
    before: photo("imprinted-patio-before", "imprinted-patio-before", "Pattern-imprinted concrete before restoration"),
    after: photo("imprinted-patio-after", "imprinted-patio-after", "Pattern-imprinted concrete after restoration"),
    caption: "Pattern-imprinted concrete restoration.",
  },
  {
    id: "block-herringbone",
    title: "Block paving",
    before: photo("block-herringbone-before", "block-herringbone-before", "Block paving before restoration"),
    after: photo("block-herringbone-after", "block-herringbone-after", "Block paving after restoration"),
    caption: "Block paving restoration.",
  },
  {
    id: "car-park",
    title: "Car park",
    before: photo("car-park-before", "car-park-before", "Tarmac car park before restoration"),
    after: photo("car-park-after", "car-park-after", "Tarmac car park after restoration"),
    caption: "Tarmac restoration on a car park.",
  },
  {
    id: "imprinted-drive",
    title: "Imprinted drive",
    before: photo("imprinted-drive-before", "imprinted-drive-before", "Pattern-imprinted driveway before restoration"),
    after: photo("imprinted-drive-after", "imprinted-drive-after", "Pattern-imprinted driveway after restoration"),
    caption: "Pattern-imprinted concrete restoration.",
  },
  {
    id: "tarmac-approach",
    title: "Tarmac approach",
    before: photo("tarmac-approach-before", "tarmac-approach-before", "Tarmac approach before restoration"),
    after: tarmacApproachAfter,
    caption: "Tarmac restoration.",
  },
  {
    id: "block-seal",
    title: "Wet-look seal",
    before: photo("block-seal-before", "block-seal-before", "Block paving before a wash and wet-look seal"),
    after: photo("block-seal-after", "block-seal-after", "Block paving after a wash and wet-look seal"),
    caption: "Block paving after a wash and wet-look seal.",
  },
];

export function serviceMedia(slug: string): MediaAsset | undefined {
  if ((PENDING_SERVICE_IMAGES as readonly string[]).includes(slug)) {
    return undefined;
  }
  return MEDIA.services[slug as keyof typeof MEDIA.services];
}
