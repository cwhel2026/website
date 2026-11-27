"use client";

import Image from "next/image";
import { useCallback, useRef, useState } from "react";
import type { MediaAsset } from "@/lib/media-assets";

type Props = {
  before: MediaAsset;
  after: MediaAsset;
  beforeLabel?: string;
  afterLabel?: string;
  caption: string;
  priority?: boolean;
};

function SlideImage({ asset, sizes, priority }: { asset: MediaAsset; sizes: string; priority: boolean }) {
  return (
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
  );
}

export function BeforeAfterSlider({
  before,
  after,
  beforeLabel = "Before",
  afterLabel = "Illustrative",
  caption,
  priority = false,
}: Props) {
  const [pct, setPct] = useState(50);
  const dragging = useRef(false);

  const move = useCallback((clientX: number, rect: DOMRect) => {
    const x = Math.min(Math.max(clientX - rect.left, 0), rect.width);
    setPct((x / rect.width) * 100);
  }, []);

  const sizes = "(max-width: 768px) 100vw, 560px";

  return (
    <figure className="space-y-3">
      <div
        className="relative aspect-[16/10] w-full cursor-col-resize touch-none select-none overflow-hidden border border-white/10 bg-brand-ink"
        role="slider"
        aria-label="Compare the reference photograph with the illustrative treatment"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(pct)}
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "ArrowLeft") setPct((value) => Math.max(0, value - 5));
          if (e.key === "ArrowRight") setPct((value) => Math.min(100, value + 5));
        }}
        onPointerDown={(e) => {
          dragging.current = true;
          (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
          move(e.clientX, e.currentTarget.getBoundingClientRect());
        }}
        onPointerMove={(e) => {
          if (!dragging.current) return;
          move(e.clientX, e.currentTarget.getBoundingClientRect());
        }}
        onPointerUp={(e) => {
          dragging.current = false;
          try {
            (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
          } catch {
            /* ignore */
          }
        }}
      >
        <SlideImage asset={before} sizes={sizes} priority={priority} />
        <div className="absolute inset-0" style={{ clipPath: `inset(0 ${100 - pct}% 0 0)` }} aria-hidden>
          <SlideImage asset={after} sizes={sizes} priority={priority} />
        </div>
        <div
          className="absolute bottom-0 top-0 z-10 w-0.5 -translate-x-1/2 bg-brand-gold"
          style={{ left: `${pct}%` }}
          aria-hidden
        />
        <div
          className="pointer-events-none absolute top-1/2 z-20 flex h-11 w-11 items-center justify-center border border-brand-gold bg-brand-ink text-xs font-semibold text-brand-gold"
          style={{ left: `${pct}%`, transform: "translate(-50%, -50%)" }}
          aria-hidden
        >
          ↔
        </div>
        <span className="absolute left-3 top-3 z-10 bg-brand-ink/80 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-white">
          {beforeLabel}
        </span>
        <span className="absolute right-3 top-3 z-10 bg-brand-gold px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-brand-ink">
          {afterLabel}
        </span>
      </div>
      <figcaption className="text-sm leading-relaxed text-brand-ink/70">{caption}</figcaption>
    </figure>
  );
}