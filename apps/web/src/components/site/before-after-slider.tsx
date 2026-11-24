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
};

export function BeforeAfterSlider({
  before,
  after,
  beforeLabel = "Before (stock illustration)",
  afterLabel = "After (stock illustration)",
  caption,
}: Props) {
  const [pct, setPct] = useState(50);
  const dragging = useRef(false);

  const move = useCallback((clientX: number, rect: DOMRect) => {
    const x = Math.min(Math.max(clientX - rect.left, 0), rect.width);
    setPct((x / rect.width) * 100);
  }, []);

  return (
    <figure className="space-y-3">
      <div
        className="relative aspect-[16/10] w-full cursor-col-resize select-none overflow-hidden rounded-lg border border-stone-line bg-asphalt-950 shadow-lift"
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
        <Image
          src={before.src}
          alt={before.alt}
          fill
          className="object-cover"
          sizes="(max-width: 768px) 100vw, 560px"
          priority
        />
        <div
          className="absolute inset-0"
          style={{ clipPath: `inset(0 ${100 - pct}% 0 0)` }}
          aria-hidden
        >
          <Image
            src={after.src}
            alt={after.alt}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, 560px"
            priority
          />
        </div>
        <div
          className="absolute bottom-0 top-0 z-10 w-1 -translate-x-1/2 bg-white shadow-lg"
          style={{ left: `${pct}%` }}
          aria-hidden
        />
        <div
          className="pointer-events-none absolute top-1/2 z-20 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border border-white/40 bg-asphalt/80 text-xs text-white"
          style={{ left: `${pct}%`, transform: "translate(-50%, -50%)" }}
          aria-hidden
        >
          ↔
        </div>
        <span className="absolute left-3 top-3 z-10 rounded bg-black/55 px-2 py-1 text-xs text-white">
          {beforeLabel}
        </span>
        <span className="absolute right-3 top-3 z-10 rounded bg-restore-dark/85 px-2 py-1 text-xs text-white">
          {afterLabel}
        </span>
      </div>
      <figcaption className="text-center text-sm leading-relaxed text-asphalt/70">{caption}</figcaption>
    </figure>
  );
}