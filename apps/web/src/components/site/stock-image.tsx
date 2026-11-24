import Image from "next/image";
import type { MediaAsset } from "@/lib/media-assets";

type Props = {
  asset: MediaAsset;
  priority?: boolean;
  className?: string;
  sizes?: string;
  aspect?: string;
};

function badgeLabel(kind: MediaAsset["kind"]): string | null {
  switch (kind) {
    case "reference":
      return "Reference photo";
    case "illustrative_derivative":
      return "Illustrative";
    case "owned_project":
      return "Our project";
    case "override":
      return null;
    default:
      return null;
  }
}

export function StockImage({
  asset,
  priority,
  className = "",
  sizes = "(max-width: 768px) 100vw, 50vw",
  aspect = "aspect-[4/3]",
}: Props) {
  const badge = badgeLabel(asset.kind);

  return (
    <figure className={`relative overflow-hidden ${aspect || ""} ${className}`}>
      <picture className="absolute inset-0 block">
        {asset.srcAvif ? <source srcSet={asset.srcAvif} type="image/avif" /> : null}
        <source srcSet={asset.srcWebp} type="image/webp" />
        <Image
          src={asset.srcWebp}
          alt={asset.alt}
          fill
          className="object-cover object-center"
          sizes={sizes}
          priority={priority}
        />
      </picture>
      {badge ? (
        <span className="absolute left-2 top-2 z-10 rounded bg-black/60 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white">
          {badge}
        </span>
      ) : null}
      <figcaption className="sr-only">
        {asset.credit}. {asset.license}.
      </figcaption>
    </figure>
  );
}