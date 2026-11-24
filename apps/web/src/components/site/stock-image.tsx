import Image from "next/image";
import type { MediaAsset } from "@/lib/media-assets";

type Props = {
  asset: MediaAsset;
  priority?: boolean;
  className?: string;
  sizes?: string;
  aspect?: string;
};

export function StockImage({
  asset,
  priority,
  className = "",
  sizes = "(max-width: 768px) 100vw, 50vw",
  aspect = "aspect-[4/3]",
}: Props) {
  return (
    <figure className={`relative overflow-hidden ${aspect || ""} ${className}`}>
      <Image
        src={asset.src}
        alt={asset.alt}
        fill
        className="object-cover"
        sizes={sizes}
        priority={priority}
      />
      {asset.kind === "stock" && (
        <span className="absolute left-2 top-2 rounded bg-black/55 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-white">
          Stock illustration
        </span>
      )}
      {asset.credit && (
        <figcaption className="sr-only">{asset.credit}</figcaption>
      )}
    </figure>
  );
}